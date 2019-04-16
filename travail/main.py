from random import randint
from time import time, sleep

def get_name():
	s = " "
	while(len(s)< 3):
		s = input("What's your name? ")
	return s

def main(name):
	s_time = time()
	points = 0
	events = []
	rand = -1

	"""while(points < 5):
		events.append(input("Enter text:"))
		if(randint(0,3) == 0):
			s = "You've won a point!!"
			points += 1
			print(s)
			events.append(s)
		sleep(0.5)"""

	while(rand != 3):
		events.append(input("Enter text:"))
		sleep(0.5)
		rand = randint(0,3)

	end_time = time()-s_time
	s = ("Well played, "+name+", you've won the game in %d s"%end_time)
	print(s)
	events.append(s)
	print("events order")
	for e_id, event in enumerate(events):
		print("\t" + str(e_id) + ":" + event)

if __name__ == "__main__":
	name = get_name()
	restart = "Y"
	while restart == "Y":
		main(name)
		restart = (input("Do you want to replay "+name+"? (Y/N)")).upper()
