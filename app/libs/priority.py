from dostoevsky.tokenization import RegexTokenizer
from dostoevsky.models import FastTextSocialNetworkModel
import numpy as np
from string import punctuation
from nltk.corpus import stopwords
import nltk
import gensim.downloader as download_api
from navec import Navec
from slovnet import Morph
from natasha import Segmenter, MorphVocab, NewsEmbedding, NewsMorphTagger, Doc

from models.event import EventCalendar

TAGGER_EMBEDDINGS = "navec_news_v1_1B_250K_300d_100q.tar"
TAGGER_MODEL = "slovnet_morph_news_v1.tar"
CUDA_STATE = -1

ORDINARY_LOWER_BOUND = 0
ORDINARY_UPPER_BOUND = 1.0 / 3
IMPORTANT_LOWER_BOUND = 2.0 / 3
IMPORTANT_UPPER_BOUND = 1

class TextProcessingStuff:
  punctuation += '«»—'

  nltk.download("stopwords")
  russian_stopwords = stopwords.words("russian")

  segmenter = Segmenter()
  morph_vocab = MorphVocab()

  emb = NewsEmbedding()
  morph_tagger = NewsMorphTagger(emb)

  @classmethod
  def preprocess_text(cls, text):
    doc = Doc(text)
    doc.segment(cls.segmenter)
    doc.tag_morph(cls.morph_tagger)
    clean_text = np.array([])
    for token in doc.tokens:
      token.lemmatize(cls.morph_vocab)
      if token.lemma not in punctuation and token.lemma not in cls.russian_stopwords:
        clean_text = np.append(clean_text, token.lemma)
    return clean_text

class EmotionExtractor:  # checks the emotional importance
  dostoevsky_tokenizer = RegexTokenizer()
  dostoevsky_model = FastTextSocialNetworkModel(tokenizer=dostoevsky_tokenizer)

  class InvalidTextsArgument(Exception):
    """
    Input texts must be either list of strings or standalone string
    """
    def __init__(self, message='Input texts must be either list of strings or standalone string'):
        super().__init__(message)
  
  @classmethod
  def get_tonality(cls, texts):
    if isinstance(texts, str):
      texts = [texts]
    elif not isinstance(texts, list):
      raise cls.InvalidTextsArgument
    
    texts_tonality = cls.dostoevsky_model.predict(texts)
    
    emotional_powers = []

    for text_tonality in texts_tonality:
      current_emotional_power = text_tonality['negative'] * text_tonality['positive']
      emotional_powers.append(current_emotional_power)
    
    return emotional_powers


class LogicalImportanceExtractor:  # looks for important events markers
  russian_model = download_api.load('word2vec-ruscorpora-300')  # emdeddings

  navec = Navec.load(TAGGER_EMBEDDINGS)  # embeddings for tagger
  morph = Morph.load(TAGGER_MODEL, batch_size=4)  # tagger
  morph.navec(navec)

  _importance_signs = [
                             'важно', 'срочно', 'необходимо', 'безотлагательно',
                             'серьёзно', 'внимание', 'быстрее', 'спешно',
                             'не забыть', 'экстренно', 'критично', 'семья', 'родители', 'мама', 'папа',
                             'брат', 'сестра', 'бабушка', 'дедушка', 'ВсеРоссийский',
                             'Всемирный', 'международный', 'экзамен', 
                             'собеседование', 'интервью', 'ответственное', 
                             'поручение', 'босс', 'шеф', 'начальство', 'чрезвычайно',
                             'руководитель', 'директор', 'ректор', 'декан', 'преподаватель',
                             'препод', 'профессор', 'проверка', 'финальный', 'конкурс',
                             'защита', 'олимпиада', 'соревнование', 'конференция',
                             'выступление', 'итоговый', 'проект', 'симпозиум',
                             'семинар', 'скорее', 'актуально', 'контрольная', 'командировка',
                             'суд', 'концерт', 'государство', 'врач', 'обследование',
                             'совещание', 'начальник', 'чп', 'чс', 'кубок', 'чемпионат', 'первенство',
                             'документы', 'рабочий', 'созвон', 'паспорт'
                      ]

  @classmethod
  def word_to_wordtag(cls, word):
    markup = next(cls.morph.map([[word]]))
    tag = markup.tokens[0].tag.split('|')[0]
    return f'{word}_{tag}'
  
  @classmethod
  def get_2words_similariry(cls, word1, word2):
    if word1 == word2:
      return 1
    word1, word2 = cls.word_to_wordtag(word1), cls.word_to_wordtag(word2)
    if word1 not in cls.russian_model.vocab.keys():
      return 0
    if word2 not in cls.russian_model.vocab.keys():
      return 0
    return cls.russian_model.similarity(word1, word2)
  
  @classmethod
  def get_word_importance_mark(cls, word):
    importance = 0
    for importance_marker in cls._importance_signs:
      importance = max(importance, cls.get_2words_similariry(importance_marker, word))
    return importance
  
  @classmethod
  def get_importance(cls, text):
    text = TextProcessingStuff.preprocess_text(text)
    importance = 0
    for token in text:
      importance = max(importance, cls.get_word_importance_mark(token))
    return importance


class PriorityEstimator:
  @classmethod
  def get_text_priority(cls, text: str):
    emotional_importance = EmotionExtractor.get_tonality(text)[0]
    logical_importance = LogicalImportanceExtractor.get_importance(text)
    return max(emotional_importance, logical_importance)
  
  @classmethod
  def get_event_priority(cls, event: EventCalendar):
    cumulative_text = event.title
    if event.description:
        cumulative_text += event.description
    importance_num = cls.get_text_priority(cumulative_text)
    return importance_num
