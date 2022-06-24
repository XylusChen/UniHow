import time

class UserTimer:
  INTERVAL = 300 # 5 minutes, number of seconds.
  
  def __init__(self, userID, currentTime):
    self.userID = userID
    self.lastInputTime = currentTime

  def canSend(self):
    return (time.time() - self.lastInputTime) > UserTimer.INTERVAL
    
  def timeTillSend(self):
    timeLeft = round(300 - (time.time() - self.lastInputTime))
    if timeLeft > 0:
      return timeLeft
    else:
      return 0