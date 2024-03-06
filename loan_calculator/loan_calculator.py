import os
import platform
import json
import decimal

with open('messages.json', 'r') as file:
    MESSAGES = json.load(file)


def clear_screen():
    """
    Clears the user's terminal screen.
    """

    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def prompt(message="", *, key=None, args=None):
    prefix = ">>"

    if key and args:
        message = f"{prefix} {MESSAGES[key].format(**args)}"
    elif key:
        message = f"{prefix} {MESSAGES[key]}"
    else:
        message = f"{prefix} {message}"

    print(message)


def prompt_error(key, args=None):
    """
    Displays a prefixed error message that is padded by newlines.
    This function can:
    1. Retrieve and display messages based on a key from the 'messages.json'
       JSON file.
    2. Retrieve, format and display messages based on a key and format
       arguments from the 'messages.json' file.
    """

    if args:
        message = MESSAGES[key].format(**args)
    else:
        message = MESSAGES[key]

    print(f"\nERROR: {message} Try again. \n")


def prompt_enter_to_continue():
    print()
    print(">> Press enter to continue.", end='')
    input()


def determine_error_message(user_response, input_type):
    if not user_response:
        error_message_key = "empty_" + input_type
    elif not invalid_number(user_response):
        number = decimal.Decimal(user_response)
        if not number and (input_type == "loan_amount"):
            error_message_key = "zero_" + input_type
        else:
            error_message_key = "negative_" + input_type
    else:
        error_message_key = "invalid_" + input_type

    return error_message_key


def invalid_number(number_str):
    if number_str in ("nan", "inf", "-inf"):
        return True

    try:
        decimal.Decimal(number_str)
    except decimal.InvalidOperation:
        return True

    return False


def is_valid_input(input_str, input_type):
    def is_zero_or_greater():
        return (
            not invalid_number(input_str) and
            decimal.Decimal(input_str) >= 0
        )

    def is_valid_loan_amount():
        return (
            not invalid_number(input_str) and
            decimal.Decimal(input_str) > 0
        )

    def is_valid_loan_duration():
        is_empty = not input_str
        return is_zero_or_greater() or is_empty

    def is_valid_loan_apr():
        return is_zero_or_greater()

    match input_type:
        case "amount":
            return is_valid_loan_amount()
        case "duration":
            return is_valid_loan_duration()
        case "apr":
            return is_valid_loan_apr()


def request_loan_amount():
    while True:
        prompt(key="enter_loan_amount")
        response = input("$").replace(",", '').replace("$", '')

        if is_valid_input(response, "amount"):
            break

        error_msg = determine_error_message(response, "loan_amount")
        if error_msg == "invalid_loan_amount":
            prompt_error(key=error_msg, args={"loan_amt":response})
        else:
            prompt_error(key=error_msg)

    return decimal.Decimal(response)


def request_loan_duration(duration_type):
    while True:
        response = input(f"{duration_type.capitalize()}s: ")

        if is_valid_input(response, "duration"):
            break

        error_msg = determine_error_message(response, "loan_duration")

        match error_msg:
            case "negative_loan_duration":
                format_args = {"duration_type": duration_type}
            case "invalid_loan_duration":
                format_args = {
                    "response": response,
                    "duration_type": duration_type,
                }

        prompt_error(key=error_msg, args=format_args)

    response = response or 0
    return decimal.Decimal(response)


def total_loan_months():
    while True:
        prompt(key="enter_loan_duration")
        years = request_loan_duration("year")
        months = request_loan_duration("month")
        total_months = (years * 12) + months

        if total_months > 0:
            break

        prompt_error(key="empty_loan_duration")

    return total_months


def request_loan_apr():
    while True:
        prompt(key="enter_apr")
        response = input("APR %: ").replace("%", "")

        if is_valid_input(response, "apr"):
            break

        error_msg = determine_error_message(response, "apr")

        match error_msg:
            case "invalid_apr":
                prompt_error(key=error_msg, args={"response": response})
            case _:
                prompt_error(key=error_msg)

    response = response or 0
    return decimal.Decimal(response)


def request_loan_details():
    loan_amount = request_loan_amount()

    print()
    loan_months = total_loan_months()

    print()
    loan_apr = request_loan_apr()

    return {
        "amount": loan_amount,
        "months": loan_months,
        "apr_percent": loan_apr,
    }


def calculate_loan_results(amount, months, apr_percent):
    def monthly_interest_rate():
        apr_decimal = apr_percent / 100
        return apr_decimal / 12

    def monthly_payment():
        interest_rate = monthly_interest_rate()

        if not interest_rate:
            return amount / months

        return amount * (interest_rate / (1 - (1 + interest_rate)**(-months)))

    def loan_total():
        return monthly_payment() * months

    def interest_total():
        return loan_total() - amount

    return {
        "number_of_payments": months,
        "monthly_payment": monthly_payment(),
        "interest_total": interest_total(),
        "loan_total": loan_total(),
    }


def display_greeting():
    greeting = "\n".join(MESSAGES["welcome"])
    prompt(greeting)
    prompt_enter_to_continue()


def display_results(loan_terms, loan_calculations):
    print(f"{" LOAN TERMS ":-^30}")
    print(f"Loan Amount: ${loan_terms["amount"]:,}")
    print(f"Loan Duration: {loan_terms["months"]:,} months")
    print(f"Annual Percentage Rate (APR): {loan_terms["apr_percent"]:,}%")

    print()

    print(f"{" RESULTS ":-^30}")
    print(f"Monthly Payment: ${loan_calculations["monthly_payment"]:,.02f}")
    print(f"Total of {loan_calculations["number_of_payments"]:,} Payments: "
          f"${loan_calculations["loan_total"]:,.02f}"
    )
    print(f"Total Interest: ${loan_calculations["interest_total"]:,.02f}")


def start_program():
    clear_screen()
    display_greeting()

    while True:
        clear_screen()
        loan_terms = request_loan_details()
        loan_calculations = calculate_loan_results(**loan_terms)

        clear_screen()
        display_results(loan_terms, loan_calculations)

        print("\n")
        prompt(key="calculate_again")
        calculate_again = input()

        if calculate_again.lower() in ("q", "quit"):
            print()
            prompt(key="goodbye")
            break


start_program()
