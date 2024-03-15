import json
import os
import platform
import random
import sys
from time import sleep

SETTINGS = {
    "opponent_name": "Monty",
    "scoreboard_width": 23,
    "points_to_win": 3
}

RULES = ["Win a round to earn one point",
         "No points are awarded if a tie occurs",
        f"First to reach {SETTINGS["points_to_win"]} points wins the match"]

COMMANDS = {"help": "h", "quit": "q!"}

MOVES = {
    "rock": {"alias": "r", "beats": ["scissor", "lizard"]},
    "paper": {"alias": "p", "beats": ["rock", "spock"]},
    "scissor": {"alias": "s", "beats": ["paper", "lizard"]},
    "spock": {"alias": "k", "beats": ["rock", "scissor"]},
    "lizard": {"alias": "l", "beats": ["paper", "spock"]},
}

with open("messages.json", "r") as file:
    MESSAGES = json.load(file)

def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def prompt(*messages, key=None, kwargs=None, prefix=">>", end="\n"):
    """
    Prints values to sys.stdout. If no arguments are passed, nothing will be
    printed.

    *messages
      zero or more objects to be printed
    key
      key value from MESSAGES; used to retrieve the respective
      message
    kwargs
      a dictionary object used to format the values from MESSAGES;
      dictionary key names must match the values enclosed in curly braces
    prefix
      string prepended to values
    end
      string appended after the last value, default a newline
    """

    if key and kwargs:
        print(f"{prefix} {MESSAGES[key].format(**kwargs)}", end=end)
    elif key:
        print(f"{prefix} {MESSAGES[key]}", end=end)
    else:
        for message in messages:
            print(f"{prefix} {message}", end=end)


def prompt_enter_to_continue(allow_command=True):
    print()
    prompt("Enter any key to continue.", end="")
    user_input = input().lower()

    if allow_command and get_input_type(user_input) == "command":
        process_command(user_input)


def is_valid_input(input_str):
    moves = [*MOVES.keys(), *(move["alias"] for move in MOVES.values())]
    commands = [*COMMANDS.keys(), *(alias for alias in COMMANDS.values())]
    valid_inputs = moves + commands

    return input_str in valid_inputs


def get_input_type(input_str):
    if not is_valid_input(input_str):
        return "invalid"

    commands = list(COMMANDS.keys()) + list(COMMANDS.values())
    if input_str in commands:
        return "command"

    return "move"


def expand_move_abbreviation(alias):
    for move, details in MOVES.items():
        if alias == details["alias"]:
            return move

    return alias


def generate_description(category):
    def moves():
        return [f"{move} ({', '.join(details["alias"])})"
                for move, details in MOVES.items()]

    def commands():
        return [f"{command} ({alias})"
                for command, alias in COMMANDS.items()]

    def winning_moves():
        return [f"{move.capitalize()} beats {' and '.join(details["beats"])}"
                for move, details in MOVES.items()]

    def rules():
        return winning_moves() + RULES

    def all_inputs():
        return moves() + commands()

    match category:
        case "moves":
            return moves()
        case "winning_moves":
            return winning_moves()
        case "rules":
            return rules()
        case "all_inputs":
            return all_inputs()


def display_help():
    prompt("RULES")
    prompt(*generate_description("rules"), prefix="•")

    print()
    prompt("To select your move, please enter the complete word (eg., 'rock') "
           "or one of the following letters:",
           ', '.join(generate_description("moves")))

    print()
    prompt("You may quit playing at anytime by entering 'q!' or 'quit'",
           "Enter 'h' or 'help' to see this message again.")


def display_introduction(returning_user=False):
    clear_screen()

    if returning_user:
        prompt(key="welcome_back")
    else:
        prompt(key="welcome")
        prompt(
            key="opponent_greeting",
            kwargs={"opponent_name": SETTINGS["opponent_name"]}
        )
        prompt_enter_to_continue(False)

        clear_screen()
        display_help()

    prompt_enter_to_continue()


def display_valid_choices():
    options = ', '.join(generate_description("all_inputs"))
    prompt(f"Options: {options}")


def display_invalid_input_message(input_str):
    print(
        f"ERROR: '{input_str}' isn't a valid choice."
        "You may choose from the following options:"
    )
    display_valid_choices()


def display_round_results(game, user_move, opponent_move):
    opponent = SETTINGS["opponent_name"]
    winner = game["round_winner"]

    format_args = {
        "player_move": user_move.upper(),
        "opponent_name": opponent,
        "opponent_move": opponent_move.upper()
    }
    prompt(key="round_results", kwargs=format_args, end="\n\n")

    if winner == "user":
        prompt(key="user_wins_round")
    elif winner == opponent:
        prompt(key="opponent_wins_round", kwargs={"name": opponent})
    else:
        prompt(key="round_tied")

    prompt_enter_to_continue()


def display_scoreboard(game):
    def display_header(border_char):
        if game["tiebreaker_round"]:
            header = " TIEBREAKER ROUND "
        else:
            header = f" ROUND {game["current_round"]} "

        print(f"{header:{border_char}^{SETTINGS["scoreboard_width"]}}")

    def display_scores():
        column_width = SETTINGS["scoreboard_width"] // 2
        player = f"You: {game["user_score"]}"
        opponent = f"{SETTINGS["opponent_name"]}: {game["opponent_score"]}"

        print(f"{player:<{column_width}}|{opponent:>{column_width}}")

    border = '-'
    display_header(border)
    display_scores()
    print(border * SETTINGS["scoreboard_width"])
    print()


def display_game_results(game):
    display_scoreboard(game)

    prompt(key="winner_detected", end="\n\n")
    sleep(1)

    prompt(key="drumroll", prefix="", end="\n\n")
    sleep(1)

    if game["grand_winner"] == "user":
        prompt(key="user_grand_winner", prefix='')
    else:
        prompt(key="opponent_grand_winner",
               kwargs={"opponent_name": SETTINGS["opponent_name"]},
               prefix='')

    prompt_enter_to_continue()


def create_game():
    return {
        "current_round": 1,
        "tiebreaker_round": False,
        "user_score": 0,
        "opponent_score": 0,
        "round_winner": None,
        "grand_winner": None,
    }


def process_command(command):
    if command in ("help", "h"):
        clear_screen()
        display_help()
        prompt_enter_to_continue()
    else:
        clear_screen()
        exit_program()


def process_moves(game, user_move, opponent_move):
    if len(user_move) == 1:
        user_move = expand_move_abbreviation(user_move)

    process_round(game, user_move, opponent_move)

    clear_screen()
    display_scoreboard(game)
    display_round_results(game, user_move, opponent_move)


def process_round(game, user_move, opponent_move):
    def determine_round_winner():
        winner = None

        if opponent_move in MOVES[user_move]["beats"]:
            winner = "user"
        if user_move in MOVES[opponent_move]["beats"]:
            winner = SETTINGS["opponent_name"]

        return winner

    def determine_grand_winner():
        if game["user_score"] > 2:
            return "user"

        if game["opponent_score"] > 2:
            return SETTINGS["opponent_name"]

        return None

    def increment_score(winner):
        if winner == "user":
            game["user_score"] += 1
        if winner == SETTINGS["opponent_name"]:
            game["opponent_score"] += 1

    game["current_round"] += 1

    winner = determine_round_winner()
    increment_score(winner)

    game["round_winner"] = winner
    game["grand_winner"] = determine_grand_winner()

    game["tiebreaker_round"] = (
        (game["user_score"] == 2) and
        (game["opponent_score"] == 2)
    )


def get_user_input():
    while True:
        user_input = input("Your move: ").lower()

        if is_valid_input(user_input):
            return user_input

        clear_screen()
        display_invalid_input_message(user_input)
        prompt_enter_to_continue()


def play_round(game):
    while True:
        display_scoreboard(game)
        display_valid_choices()

        user_input = input("Your move: ").lower()
        input_type = get_input_type(user_input)

        if input_type == "move":
            opponent_move = random.choice(list(MOVES))
            process_moves(game, user_input, opponent_move)
            break

        if input_type == "command":
            process_command(user_input)
        else:
            clear_screen()
            display_invalid_input_message(user_input)
            prompt_enter_to_continue()

        clear_screen()


def play_game():
    game = create_game()

    while not game["grand_winner"]:
        clear_screen()
        play_round(game)

    clear_screen()
    display_game_results(game)


def start_program():
    display_introduction()

    while True:
        play_game()

        clear_screen()
        prompt(key="play_again")
        prompt_enter_to_continue()

        clear_screen()
        prompt(key="welcome_back")
        prompt_enter_to_continue()


def exit_program():
    prompt(
        key="goodbye",
        kwargs={"opponent_name": SETTINGS["opponent_name"]},
        prefix="\n>>",
        end="\n\n"
    )
    sys.exit()


start_program()
