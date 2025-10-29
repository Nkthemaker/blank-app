import streamlit as st
import random
import math
import numpy as np  # Used for the more complex percentage type
import time  # Added for timer functionality

# --- Constants and Configuration ---
SQUARE_RANGE = (1, 50)
CUBE_RANGE = (1, 20)
PERCENTAGE_BASE_RANGE = (100, 1000)
QUIZ_DURATION_SECONDS = 60  # New constant for the timed challenge duration

st.set_page_config(layout="wide", page_title="Daily Drill Master")


# --- 1. Initialization and Session State Management ---

def initialize_session_state():
    """Initializes all necessary session state variables."""
    if 'score' not in st.session_state:
        st.session_state.score = 0
    if 'mode' not in st.session_state:
        st.session_state.mode = 'square'  # Default mode
    if 'current_q' not in st.session_state:
        st.session_state.current_q = None
    if 'correct_ans' not in st.session_state:
        st.session_state.correct_ans = None
    if 'feedback' not in st.session_state:
        st.session_state.feedback = ""
    if 'question_counter' not in st.session_state:
        st.session_state.question_counter = 0

    # New state variables for the Timed Quiz
    if 'quiz_start_time' not in st.session_state:
        st.session_state.quiz_start_time = 0.0
    if 'quiz_ended' not in st.session_state:
        st.session_state.quiz_ended = False
    if 'is_timed_mode' not in st.session_state:
        st.session_state.is_timed_mode = False

    # NEW: Initialize the text input content state explicitly for manual clearing
    if 'current_user_input' not in st.session_state:
        st.session_state.current_user_input = ""


def set_mode(new_mode, is_timed=False):
    """Changes the practice mode and resets the quiz state."""
    st.session_state.mode = new_mode
    st.session_state.score = 0
    st.session_state.feedback = ""
    st.session_state.question_counter = 0
    # Reset timer states
    st.session_state.quiz_start_time = 0.0
    st.session_state.quiz_ended = False
    st.session_state.is_timed_mode = is_timed

    # NEW: Clear input on mode change
    st.session_state.current_user_input = ""

    # Generate the first question for the new mode
    generate_new_question()


# --- 2. Question Generation Functions ---

def generate_square_q():
    """Generates a random square question (N^2)."""
    N = random.randint(*SQUARE_RANGE)
    question = f"What is the **square** of **{N}**?"
    answer = N * N
    return question, answer


def generate_cube_q():
    """Generates a random cube question (N^3)."""
    N = random.randint(*CUBE_RANGE)
    question = f"What is the **cube** of **{N}**?"
    answer = N * N * N
    return question, answer


def generate_percentage_q():
    """Generates a random percentage question (X% of Y)."""
    # Use common competitive exam percentages for mental calculation focus
    common_percents = [5, 10, 15, 20, 25, 30, 40, 50, 75, 12.5, 33.33, 66.66]
    percent = random.choice(common_percents)

    # Ensure the base number is often a multiple of 10 or 100 for clean numbers
    if percent in [12.5, 33.33, 66.66]:
        # For fractional equivalents, pick a base number that simplifies the calculation
        if percent == 12.5:  # 1/8
            Y = random.choice(range(8, 500, 8))
        elif percent == 33.33:  # 1/3
            Y = random.choice(range(3, 500, 3))
        else:  # 66.66 ~ 2/3
            Y = random.choice(range(3, 500, 3))
        percent_str = f"$$\\mathbf{{{percent:.2f}\\%}}$$"
    else:
        # Standard clean number percentage
        Y = random.choice(range(100, 1000, 10))
        percent_str = f"**{percent}%**"

    question = f"Calculate {percent_str} of **{Y}**."

    # Calculate the exact answer, rounding percentages that are repeating fractions
    answer = (percent / 100) * Y

    # Round the answer if the percent was a repeating decimal to ensure a clean integer/float match
    if percent in [33.33, 66.66, 12.5]:
        answer = round(answer, 2)

    return question, answer


def generate_mixed_q():
    """Generates a random question from all modes for the timed challenge."""
    mode_funcs = [generate_square_q, generate_cube_q, generate_percentage_q]
    q_func = random.choice(mode_funcs)
    return q_func()


def generate_new_question():
    """Calls the appropriate generator based on the current mode and updates state."""

    if st.session_state.mode == 'square':
        q, a = generate_square_q()
    elif st.session_state.mode == 'cube':
        q, a = generate_cube_q()
    elif st.session_state.mode == 'percentage':
        q, a = generate_percentage_q()
    elif st.session_state.mode == 'mixed':
        q, a = generate_mixed_q()
    else:
        q, a = "Select a mode in the sidebar.", 0

    st.session_state.current_q = q
    st.session_state.correct_ans = a
    st.session_state.question_counter += 1


# --- 3. Answer Checking and Skipping Logic ---

# NEW: Wrapper function to handle answer check and clearing the input box
def handle_check_answer():
    # Get the value from the session state key associated with the text input
    user_input = st.session_state.current_user_input

    # Pass the input to the core check logic
    check_answer(user_input)

    # CRITICAL FIX: Explicitly reset the input's value state after checking
    st.session_state.current_user_input = ""


def check_answer(user_input):
    """Compares the user's input with the correct answer and updates state/score."""

    # Check if quiz has ended before processing answer
    if st.session_state.quiz_ended and st.session_state.is_timed_mode:
        st.session_state.feedback = f"🚨 Time's up! Your final score was {st.session_state.score}."
        return

    if user_input is None or user_input == "":
        st.session_state.feedback = "🚨 Please enter an answer before submitting."
        # Crucial fix: Do not generate new question if input is empty
        return

    # Attempt to convert user input to a float for comparison
    try:
        user_ans = float(user_input)
    except ValueError:
        st.session_state.feedback = "❌ Invalid input. Please enter a numerical value."
        # Crucial fix: Do not generate new question if input is invalid
        return

    correct_ans = st.session_state.correct_ans

    # Use a small tolerance for float comparison, especially for percentages
    tolerance = 0.01

    if abs(user_ans - correct_ans) < tolerance:
        # Correct Answer
        st.session_state.score += 1
        st.session_state.feedback = f"✅ **Correct!** Great job on that **{st.session_state.mode}** drill."

    else:
        # Wrong Answer - Show the correct answer
        # Use simple integer if the correct answer is an integer, otherwise display float
        display_ans = int(correct_ans) if correct_ans == int(correct_ans) else correct_ans
        st.session_state.feedback = f"❌ **Wrong.** The correct answer was: **{display_ans}**."

    # Generate the next question immediately after checking
    generate_new_question()


# NEW: Wrapper function to handle skipping and clearing the input box
def handle_skip_question():
    skip_question()
    # CRITICAL FIX: Explicitly reset the input's value state after skipping
    st.session_state.current_user_input = ""


def skip_question():
    """Skips the current question and generates the next one."""

    # Use simple integer if the correct answer is an integer, otherwise display float
    correct_ans = st.session_state.correct_ans
    display_ans = int(correct_ans) if correct_ans == int(correct_ans) else correct_ans

    # Update feedback to show that the question was skipped and provide the answer
    st.session_state.feedback = f"⏭️ **Skipped.** The correct answer was: **{display_ans}**."

    # Generate the next question
    generate_new_question()


# --- 4. Streamlit UI Layout (The main changes happen here) ---

initialize_session_state()

st.title("🧠 Daily Drill Master")
st.markdown("Practice your Squares, Cubes, and Percentages to boost your competitive exam speed!")

# Sidebar for Mode Selection
st.sidebar.header("Individual Drills")
st.sidebar.button("Square Drills", on_click=set_mode, args=('square', False), use_container_width=True)
st.sidebar.button("Cube Drills", on_click=set_mode, args=('cube', False), use_container_width=True)
st.sidebar.button("Percentage Drills", on_click=set_mode, args=('percentage', False), use_container_width=True)

# New section for Timed Quiz in the sidebar
st.sidebar.markdown("---")
st.sidebar.header("Timed Challenge")
if st.sidebar.button(f"Start {QUIZ_DURATION_SECONDS} Second Mixed Drill", type="primary", use_container_width=True):
    set_mode('mixed', is_timed=True)
    st.session_state.quiz_start_time = time.time()
    # No need for st.rerun here, the app reruns on button click anyway

# Main Content Area
col1, col2 = st.columns([3, 1])

with col1:
    st.header(
        f"Mode: {st.session_state.mode.replace('square', 'Squares').replace('cube', 'Cubes').replace('percentage', 'Percentages').replace('mixed', 'Mixed Timed Drill')}")
    st.markdown("---")

    # Check if a question exists, if not, generate the first one
    if st.session_state.current_q is None:
        generate_new_question()

    st.subheader(f"Question #{st.session_state.question_counter}")
    st.markdown(f"### {st.session_state.current_q}")

    # --- REPLACED st.form with standard st.text_input and st.button for manual state control ---

    # Input for the user's answer (key holds the value, value binds it to the state)
    st.text_input(
        label="Your Answer:",
        placeholder="Type your number here...",
        # KEY holds the value in session state (must be unique)
        key="current_user_input",
        autocomplete="off",
        # VALUE is controlled by the session state variable
        value=st.session_state.current_user_input,
        disabled=st.session_state.quiz_ended and st.session_state.is_timed_mode
    )

    # Submit button (uses the new handler to check and clear)
    st.button(
        label="Check Answer",
        on_click=handle_check_answer,  # Use wrapper to check and clear
        type="primary",
        use_container_width=True,
        disabled=st.session_state.quiz_ended and st.session_state.is_timed_mode
    )

    # Skip button (uses the new handler to skip and clear)
    st.button(
        label="Skip Question ⏭️",
        on_click=handle_skip_question,  # Use wrapper to skip and clear
        use_container_width=True,
        disabled=st.session_state.quiz_ended and st.session_state.is_timed_mode
    )
    # -----------------------------------------------------------------------------------------

with col2:
    st.subheader("Your Score")
    st.metric(
        label="Correct Answers",
        value=st.session_state.score,
        delta=f"Out of {st.session_state.question_counter - 1} Attempts",
        delta_color="off"
    )

    # Timer Display Logic (NEW)
    if st.session_state.is_timed_mode and st.session_state.quiz_start_time > 0:
        elapsed_time = time.time() - st.session_state.quiz_start_time
        time_left = max(0, QUIZ_DURATION_SECONDS - int(elapsed_time))

        if time_left > 0 and not st.session_state.quiz_ended:
            # Display time remaining
            st.metric(label="Time Remaining", value=f"{time_left}s", delta="Hurry!", delta_color="inverse")

            # This is key for the timer: Rerun the script every second to update the timer display
            time.sleep(1)
            st.rerun()

        elif time_left <= 0 and not st.session_state.quiz_ended:
            # End the quiz
            st.session_state.quiz_ended = True
            st.balloons()
            st.warning(f"⏰ Time is up! You scored {st.session_state.score} in {QUIZ_DURATION_SECONDS} seconds.")

        elif st.session_state.quiz_ended:
            st.warning(f"Quiz ended. Final Score: {st.session_state.score}")

# Feedback Section (outside the columns for better visibility)
st.markdown("---")
st.info(st.session_state.feedback or "Start with your first question or try the Timed Challenge!")
