#! /usr/bin/python3

"""A program to play connect4. Yay!"""

import time
import random
import re
import sys
from random import choice


class Board(list):
	"""A board for playing connect4."""

	def __init__(self):

		# Initialize empty board
		for row in range(6):
			self.append([' ', ' ', ' ', ' ', ' ', ' ', ' '])

		# A counter to see how many board positions we've considered overall. Data! :D
		self.count = 0

		# Generate a dictionary of all the 4-long lines that pass through each field
		# on the board. (Used for checking the board for winners.)
		self.line_dict = generate_line_dict()
		
		# The board keeps track of what the last move was.
		self.last_move = None

		# A dictionary of solved positions (to speed up deep think-ahead).
		self.book = {}



	def get_legal_moves(self):
		"""Returns a list of legal moves for the current board position."""

		legal_moves = []
		for column in range(7):
			for row in range(5, -1, -1):
				if self[row][column] == ' ':
					legal_moves.append((row, column))
					break
		return legal_moves

	def check_for_winners(self):
		"""Check who won. 0 means human, 1 means computer, 2 means draw, None
		 means game isn't over yet."""	
		
		# If there was no last_move (i.e. at the start of a game),
		# then there is no winner.
	
		if self.last_move == None:
			return None

		winner = None

		# Check if a line passing through last_move has four identical symbols,
		# not counting the empty string.
		for line in self.line_dict[self.last_move]:
			if (self[line[0][0]][line[0][1]] == self[line[1][0]][line[1][1]] == 
				self[line[2][0]][line[2][1]] == self[line[3][0]][line[3][1]] != ' '):
				winner = self[line[0][0]][line[0][1]]

		if winner == 'x':
			return 0
		if winner == 'o':
			return 1

		#If there is an empty field left, the game isn't over yet.
		for column in range(7):
			if self[0][column] == ' ':
				return None 

		#Otherwise the game is a draw.
		return 2

	def display(self):
		"""Print the board in a reasonably pretty way."""

		print(" \033[4m1 2 3 4 5 6 7\033[0m") #ANSI underlined text
		for i in range(6):
			for j in range(7):
				print("|\033[4m"+self[i][j], end='')
			print("\033[0m|")

	def reset(self):
		"""Reset the board position. """

		# Reset fields.
		for row in range(6):
			for column in range(7):
				self[row][column] = ' '

		# Reset last_move.
		last_move = None

	def boardtostr(self):
		"""Turn the board position into a string, to make it hashable."""

		return ','.join([''.join(self[x]) for x in range(6)])


def generate_line_dict():
	""" Generates a dictionary mapping each field on the board to all the 4-long
	lines passing through it. """

	line_dict = {}
	for row in range(6):
		for column in range(7):
			field = (row, column)
			lines = []
			# Generate rows.
			start_column = column
			for x in range(4):
				if 0 <= start_column <= 3:
					lines.append([(row, start_column), (row, start_column + 1), (row, start_column + 2), (row, start_column + 3)])
				start_column -= 1
			# Generate columns.
			start_row = row
			for x in range(4):
				if 0 <= start_row <= 2:
					lines.append([(start_row, column), (start_row + 1, column), (start_row + 2, column), (start_row +3, column)])
				start_row -= 1
			# Generate backslash diagonals.
			start_row = row
			start_column = column
			for x in range(4):
				if 0 <= start_row <= 2 and 0 <= start_column <= 3:
					lines.append([(start_row, start_column), (start_row + 1, start_column + 1), (start_row + 2, start_column + 2), (start_row + 3, start_column + 3)])
				start_row -= 1
				start_column -= 1
			# Generate slash diagonals.
			start_row = row
			start_column = column
			for x in range(4):
				if 3 <= start_row <= 5 and 0 <= start_column <= 3:
					lines.append([(start_row, start_column), (start_row - 1, start_column + 1), (start_row - 2, start_column + 2), (start_row - 3, start_column + 3)])
				start_row += 1
				start_column -= 1
			# And finally, save the generated list to the dictionary.
			line_dict[field] = lines

	return line_dict



def get_AI_move(board, AI, AI_args):
	"""Returns the computer's move, based on the AI chosen."""

	def basic_AI(board, AI_args):
		"""An AI that uses a 'book' of known results to evaluate a position."""

		# Lookahead depth.
		depth = int(AI_args[0])
		
		def recursive_lookahead(board, depth):
			"""Returns 0 if it's an 'x'-winning position, 1 if it's an
			'o'-winning position, 2 if it's a draw, None if undecided."""
			
			if depth == 0:
				return board.check_for_winners()

			if board.player_to_move == 0:
				marker = 'x'
			if board.player_to_move == 1:
				marker = 'o'


			if depth >= 1:
				if board.check_for_winners() is not None:
					return board.check_for_winners()
				legal_moves = board.get_legal_moves()
				# A dict assigning evaluation to each possible move 
				# (0 - win for human, 1 - win for computer, 2- draw, None - undecided)
				move_results = {}
				# Swap whose turn it is, as we're about to make a move.
				# Needs to be before the "for" loop.
				board.player_to_move ^= 1
				for move in legal_moves:
					board[move[0]][move[1]] = marker
					board.last_move = move
					board.count += 1
					if ((board.boardtostr(), board.player_to_move) in board.book and
						 depth <= board.book[(board.boardtostr(), board.player_to_move)][1]):
						result = board.book[(board.boardtostr(), board.player_to_move)][0]
					else:
						result = recursive_lookahead(board, depth - 1)
					if result == board.player_to_move^1:
						board.book[(board.boardtostr(), board.player_to_move)] = (board.player_to_move^1, 42)
						move_results[move] = result
						board[move[0]][move[1]] = ' ' # Set the board the way it was before the move
						board.player_to_move ^= 1 # Keep track of whose turn it is correctly.
						return result # Short-circuit the lookahead if it's a winning move for current player.
					else:
						move_results[move] = result
					board[move[0]][move[1]] = ' '

				#Swap back whose turn it is, since we're outside the "for" loop.
				board.player_to_move ^= 1

				if board.player_to_move in move_results.values(): #If there's a winning for the player whose turn it is.
					board.book[(board.boardtostr(), board.player_to_move)] = (board.player_to_move, 42)
					return board.player_to_move
				elif 2 in move_results.values(): #If there's a move that leads to a draw.
					board.book[(board.boardtostr(), board.player_to_move)] = (2, 42)
					return 2
				elif None not in move_results.values(): #If every move leads to a win for opponent.
					board.book[(board.boardtostr(), board.player_to_move)] = (board.player_to_move^1, 42)
					return board.player_to_move^1
				else: #Not sure who wins yet.
					board.book[(board.boardtostr(), board.player_to_move)] = (None, depth)
					return None

		previous_count = board.count
		legal_moves = board.get_legal_moves()
		winning_moves = []
		non_losing_moves = []
		if board.player_to_move == 0:
			marker = 'x'
		else:
			marker = 'o'

		# Swap player as we're about to make a move.
		# This needs to be outside the "for" loop.
		board.player_to_move ^= 1
		for move in legal_moves:
			board[move[0]][move[1]] = marker
			board.last_move = move
			board.count += 1
			if (board.boardtostr(), board.player_to_move) in board.book and depth <= board.book[(board.boardtostr(), board.player_to_move)][1]:
				result = board.book[(board.boardtostr(), board.player_to_move)]
				
			else:
				result = recursive_lookahead(board, depth)
				
			if result == board.player_to_move^1: #The AI who's move it currently is.
				winning_moves.append(move)
			elif result != board.player_to_move:
				non_losing_moves.append(move)
			board[move[0]][move[1]] = ' '

		# Swap back whose turn it is, since we haven't actually made a move.
		board.player_to_move ^= 1

		#board.display()
		#print("Evaluation: Winning moves - " + str(winning_moves) + \
		#	"\nNon-losing moves - " + str(non_losing_moves) +".")


		print("Considered %s board positions to decide this move." % str(board.count - previous_count))
		if winning_moves:
			board.book[(board.boardtostr(), board.player_to_move)] = (board.player_to_move, depth)
			return random.choice(winning_moves)
		elif non_losing_moves:
			return random.choice(non_losing_moves)
		else:
			board.book[(board.boardtostr(), board.player_to_move)] = (board.player_to_move^1, depth)
			return random.choice(legal_moves)
			
	if AI == 'basic':
		if not AI_args:
			AI_args = [3] # Default lookahead depth = 3
		return basic_AI(board, AI_args)


def display_help():
	print("""
Commands:
help\t display this help
restart\t start a new game (changing who goes first)
exit\t exit the game
[number]\t move to the specified column (1, 2, 3, etc.)""")


def game_over(board, winner, first_player):
	if winner == 0: #Human
		print("Congratulations! You win.\n"
			  "To play again, enter 'restart'. To quit, enter 'exit'.")
	elif winner == 1: #Computer
		print("Computer wins.\n"
			  "To play again, enter 'restart'. To quit, enter 'exit'.")
	elif winner == 2: #Draw
		print("Game over. Draw.\n"
			  "To play again, enter 'restart'. To quit, enter 'exit'.")

	# Swapping whose turn it is, if we restart the game.
	first_player ^= 1 

	while True:
		human_input = input("Restart? Exit?: ")
		#Check the human's input for command words, in a forgiving manner.
		if re.search(r'restart', human_input, re.IGNORECASE):
			players = {0: 'Human', 1: 'Computer'}
			print("\nStarting a new game.\n"
				  "First to move: %s" % (players[first_player]))
			board.reset()
			board.display()
			return (board, first_player)		
		if re.search(r'(exit|quit)', human_input, re.IGNORECASE):
			print("Goodbye!")
			sys.exit(0)
		elif re.search(r'help', human_input, re.IGNORECASE):
			display_help()
		else:
			print("I don't understand.")


def get_human_input(board):
	while True:
		human_input = input("Your next move: ")
		#Check the human's input for command words, in a forgiving manner.
		if re.search(r'restart', human_input, re.IGNORECASE):
			return 'restart'
		elif re.search(r'(exit|quit)', human_input, re.IGNORECASE):
			return 'exit'
			sys.exit(0)
		elif re.search(r'help', human_input, re.IGNORECASE):
			return 'help'
		#Otherwise assume human meant to make a move.	
		else:
			try:
				move = int(human_input) - 1
			except ValueError:
				print("Please enter a column number to make a move, 'restart' to start"
					  "a new game, or 'exit' to quit.")
				continue #Go back to getting human input

			if move not in range(7):
				print("Invalid column number. Enter 1-7.")
				continue #Go back to getting human input

			#Check if the column has a free field left
			for row in range(5, -1, -1):
				if board[row][move] == ' ':
					return move

			print("That field is already full!")
			continue #Go back to getting human input


def play(AI, AI_args=[]):

	# Initialize empty board.
	board = Board()
	first_player = 0 # Used to determine who goes first. Changes after each 'restart' command.
	board.player_to_move = first_player

	print("\n"
		"Welcome to my Connect4 game. You are playing against the\n"
		"%s AI. To move, simply enter the\n"
		"number of the column where you wish to move. (e.g. 1)\n"
		"Enter 'exit' to quit the program, or 'restart' to start\n"
		"a new game (players alternate in moving first).\n" % AI)

	board.display()

	while True:
		if board.player_to_move == 0: #Human
			human_input = get_human_input(board)
			if human_input == 'restart':
				first_player = first_player^1
				board.player_to_move = first_player
				if first_player == 0:
					fp = 'Human'
				else:
					fp = 'Computer'
				print("Starting a new game. First to move: %s." % fp)
				board.reset()
				board.display()
				continue #go back to the start of the 'while True' loop.
			elif human_input == 'exit':
				print("Goodbye!")
				sys.exit(0)
			elif human_input == 'help':
				display_help()
			else:
				column = human_input

				# Update board
				for row in range(5, -1, -1):
					if board[row][column] == ' ':
						board[row][column] = 'x'
						board.last_move = (row, column)
						break
				
				board.display()
				if board.check_for_winners() is not None:
					winner = board.check_for_winners()
					game_over(board, winner, first_player)
					first_player ^= 1
					board.player_to_move = first_player
					continue # Go back to the start of the 'while True' loop.

				# If the game isn't over yet, it's computer's turn again.
				board.player_to_move = 1
		elif board.player_to_move == 1: #Computer
			print('\n Thinking...\n')
			move = get_AI_move(board, AI, AI_args)

			# Update board
			(row, column) = move
			board[row][column] = 'o'
			board.display()
			board.player_to_move ^= 1

			if board.check_for_winners() is not None:
				winner = board.check_for_winners()
				game_over(board, winner, first_player)
				first_player ^= 1
				board.player_to_move = first_player
				continue

			# If the game isn't over yet, it's human's turn again.
			board.player_to_move = 0


def main():
	if len(sys.argv) == 1:
		play(AI = 'basic')
	else:
		if sys.argv[1] == '--basic':
			if len(sys.argv) > 2:
				AI_args = sys.argv[2]
			else:
				AI_args = []
			play(AI = 'basic', AI_args = AI_args)
		else:
			print("Usage: connect4.py [--basic (depth)]")
			sys.exit(1)



if __name__ == '__main__':
	main()