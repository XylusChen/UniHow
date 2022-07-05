class Question:
  id_counter = 0
  
  def __init__(self, from_user, category):
    self.from_user = from_user
    self.category = category
    self.question = None
    self.status = False
    self.count = 0
    self.answer_x5collection = {}

  def update_question(self, question):
    self.question = question
    
  def update_answer(self, answered_by, answer):
    self.count += 1
    self.answer_x5collection[str(answered_by)] = answer
    if self.count >= 5 :
      self.status = True
    
  
  def get_category(self):
    return self.category

  def get_question(self):
    return self.question

  def get_status(self):
    return self.status

  def get_from_user(self):
    return self.from_user

  def get_answerx5collection(self):
    return self.answer_x5collection
  
  def get_answercount(self):
    return self.count

  def get_answer(self) :
   first_pair = list(self.answer_x5collection.items())[self.count - 1]
   return first_pair[1]

  def get_report(self) :
    return self.answer_x5collection
