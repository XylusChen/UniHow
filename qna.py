class Question:
  id_counter = 0
  
  def __init__(self, from_user, category):
    self.from_user = from_user
    self.category = category
    self.question = None
    self.status = False
    self.answered_by = None
    self.answer = None

  def update_question(self, question):
    self.question = question
    
  def update_answer(self, answered_by, answer):
    self.answered_by = answered_by
    self.answer = answer
    self.status = True
  
  def get_category(self):
    return self.category

  def get_question(self):
    return self.question

  def get_status(self):
    return self.status

  def get_answer(self):
    return self.answer

  def get_from_user(self):
    return self.from_user

  def get_answered_by(self):
    return self.answered_by
