class Question:
  def __init__(self, category):
    self.category = category
    self.question = None
    self.status = False
    self.answer = None

  def update_question(self, question):
    self.question = question
    
  def update_answer(self, answer):
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
