import time

class UserTimer:
  INTERVAL = 180 # 5 minutes, number of seconds.
  
  def __init__(self, userID, currentTime):
    self.userID = userID
    self.lastInputTime = currentTime

  def canSend(self):
    return (time.time() - self.lastInputTime) > UserTimer.INTERVAL
    
  def timeTillSend(self):
    timeLeft = round(UserTimer.INTERVAL - (time.time() - self.lastInputTime))
    if timeLeft > 0:
      return timeLeft
    else:
      return 0
