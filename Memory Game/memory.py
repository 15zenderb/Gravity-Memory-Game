import pygame
import sys
import random
import os
import csv

pygame.init()
pygame.mixer.init()

screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Memory Quiz Game")


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
DARK_RED = (139, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)

font = pygame.font.SysFont('Courier New', 36)
question_font = pygame.font.SysFont('Courier New', 36)
score_font = pygame.font.SysFont('Courier New', 48)
menu_font = pygame.font.SysFont('Courier New', 28)
fun_font = pygame.font.SysFont('Comic Sans MS', 72)
new_font = pygame.font.SysFont('Arial', 36)

base_dir = os.path.dirname(__file__)

score = 0
incorrect_answers = []
level = 1
lives = 5
questions_answered = 0
game_over = False
fall_speed = level * 0.1
questions_per_level = 5
levels_enabled = True
skipped_question = False


all_questions = []
unused_questions = []
used_questions = []

# Updated paths for sound files
sounds_dir = os.path.join(base_dir, "assets", "sounds")
correct_sound = pygame.mixer.Sound(os.path.join(sounds_dir, "correct.mp3"))
incorrect_sound = pygame.mixer.Sound(os.path.join(sounds_dir, "incorrect.mp3"))
win_sound = pygame.mixer.Sound(os.path.join(sounds_dir, "Win.wav"))
explosion_sound = pygame.mixer.Sound(os.path.join(sounds_dir, "explosion.wav"))
pause_sound = pygame.mixer.Sound(os.path.join(sounds_dir, "pause.mp3"))
unpause_sound = pygame.mixer.Sound(os.path.join(sounds_dir, "unpause.mp3"))


# Updated path for asteroid image
images_dir = os.path.join(base_dir, "assets","images")
asteroid_path = os.path.join(images_dir, "Asteroid.png")
asteroid_img = pygame.image.load(asteroid_path).convert_alpha()
asteroid_img = pygame.transform.scale(asteroid_img, (300, 300))  # Resize to 300x300 pixels
pause_bg = pygame.image.load(os.path.join(images_dir, "pause_background.jpg"))


background = None


def wait_for_input():
    """Wait for a mouse click or the Return key to resume the game."""
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                waiting = False  # Resume on mouse click
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:  # Check for both Enter and Numpad Enter
                    waiting = False  # Resume on Return or Numpad Return


def wrap_text(text, font, max_width):
    """Wraps the text into multiple lines based on the max width, then centers each line."""
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        # Test the line width with the next word
        test_line = current_line + (word + ' ') if current_line else word + ' '
        line_width, _ = font.size(test_line)  # Get the width of the line
        if line_width <= max_width:
            current_line = test_line
        else:
            # If the line exceeds max width, add the current line to the lines list
            lines.append(current_line.strip())
            current_line = word + ' '  # Start a new line with the current word

    # Add the last line, if it's not empty
    if current_line.strip():
        lines.append(current_line.strip())

    return lines

def load_high_scores():
    high_scores = []
    try:
        high_scores_file_path = os.path.join(base_dir, "high_scores.csv")
        if os.path.exists(high_scores_file_path):
            with open(high_scores_file_path, mode="r", encoding="utf-8") as file:
                csv_reader = csv.reader(file)
                for row in csv_reader:
                    if len(row) == 2: 
                        name, score = row
                        high_scores.append((name, int(score)))
    except FileNotFoundError:
        print("High scores file not found!")
    high_scores.sort(key=lambda x: x[1], reverse=True) 
    return high_scores

def load_background():
    global background
    if background is None:
        background_path = os.path.join(images_dir, "Background.jpg")
        try:
            background = pygame.image.load(background_path)
            bg_width, bg_height = background.get_size()
            aspect_ratio = bg_width / bg_height
            if screen_width / screen_height > aspect_ratio:
                new_width = int(screen_height * aspect_ratio)
                new_height = screen_height
            else:
                new_width = screen_width
                new_height = int(screen_width / aspect_ratio)

            background = pygame.transform.scale(background, (new_width, new_height))
        except FileNotFoundError:
            print("Background image not found!")


def display_high_scores():
    high_scores = load_high_scores()

    screen.fill(BLACK)

    display_text("High Scores", 0, 50, font, WHITE, center=True)

    y_offset = 100
    for i, (name, score) in enumerate(high_scores[:10]):  # Show top 10 scores
        display_text(f"{i + 1}. {name} - {score}", 0, y_offset, font, WHITE, center=True)
        y_offset += 40

    display_text("Press 'Esc' to Return", 0, screen_height - 50, font, WHITE, center=True)

    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return  

def save_high_score(name, score):
    high_scores = load_high_scores()
    high_scores.append((name, score))
    high_scores.sort(key=lambda x: x[1], reverse=True)  
    # Keep only the top 10 high scores
    high_scores = high_scores[:10]

    try:
        with open(os.path.join(base_dir, "high_scores.csv"), mode="w", encoding="utf-8") as file:
            csv_writer = csv.writer(file)
            for entry in high_scores:
                file.write(f"{entry[0]},{entry[1]}\n")
    except FileNotFoundError:
        print("Error saving high scores.")

def display_text(text, x, y, font, color, center=False):
    label = font.render(text, True, color)
    if center:
        x = (screen_width - label.get_width()) // 2
    screen.blit(label, (x, y))


def settings_menu():
    settings_running = True
    global fall_speed, questions_per_level, lives, levels_enabled, new_lives
    volume = 1.0  # Ensure volume starts at 100%
    pygame.mixer.music.set_volume(volume)  # Apply the change
    selected_index = 0

    # Define the maximum values
    max_fall_speed = 2  # Maximum fall speed
    max_lives = 100  # Maximum lives (can be changed to a more reasonable number if needed)
    max_questions_per_level = 100  # Maximum questions per level

    def display_questions_per_level():
        # Return "Infinite" as a string to display in the settings menu
        if questions_per_level == -1:
            return "Infinite"
        return str(questions_per_level)

    settings = [
        {"name": "Lives", "value": lambda: f"{lives}", "min": 1, "max": max_lives, "step": 1, "var": "lives"},
        {"name": "Levels Enabled", "value": lambda: "Yes" if levels_enabled else "No", "toggle": True, "var": "levels_enabled"},
        {"name": "Questions Per Level", "value": lambda: display_questions_per_level(), "min": 1, "max": max_questions_per_level, "step": 1, "var": "questions_per_level", "disabled": lambda: not levels_enabled},
        {"name": "Fall Speed", "value": lambda: f"{round(fall_speed * 100)}", "min": 0.05, "max": max_fall_speed, "step": 0.1, "var": "fall_speed"},
        {"name": "Volume", "value": lambda: f"{int(volume * 100)}%" if volume < 1.0 else "100%", "min": 0.0, "max": 1.0, "step": 0.1, "var": "volume"},
    ]

    def get_next_index(current_index, direction):
        next_index = (current_index + direction) % len(settings)
        while "disabled" in settings[next_index] and settings[next_index]["disabled"]():
            next_index = (next_index + direction) % len(settings)
        return next_index

    def draw_slider(screen, x, y, min_value, max_value, current_value, width=200, height=10):
        pygame.draw.rect(screen, GRAY, (x, y, width, height))  # Background
        slider_pos = (current_value - min_value) / (max_value - min_value) * width
        pygame.draw.rect(screen, YELLOW, (x + slider_pos - 5, y - 5, 10, height + 10))  # Slider knob

    is_dragging = False  # To track if the user is dragging the slider
    fall_speed_slider_y = None  # To store the y position of the Fall Speed text
    questions_per_level_slider_y = None  # To store the y position of the "Questions Per Level" slider
    lives_slider_y = None  # To store the y position of the "Lives" slider
    volume_slider_y = None  # To store the y position of the "Volume" slider

    while settings_running:
        screen.blit(pause_bg, (0, 0))  # Draw the background image (pause_bg)

        display_text("Settings", screen_width // 2, 100, fun_font, WHITE, center=True)
        
        y_offset = screen_height // 2 - (len(settings) * 25)
        
        left_column_width = screen_width // 2 - 300  # Set a reasonable distance for left column
        right_column_width = screen_width // 2 + 300  # Set a reasonable distance for right column
        
        for i, setting in enumerate(settings):
            text = setting["name"]
            value_text = f"< {setting['value']()} >"
            disabled = "disabled" in setting and setting["disabled"]()
            color = GRAY if disabled else (YELLOW if i == selected_index else WHITE)
            
            # Calculate positions to center text in each column
            left_x = left_column_width - (new_font.size(text)[0] // 2)
            right_x = right_column_width - (new_font.size(value_text)[0] // 2)

            display_text(text, left_x, y_offset, new_font, color, center=False)
            display_text(value_text, right_x, y_offset, new_font, color, center=False)

            # Capture the y position for each slider
            if "Fall Speed" in text:
                fall_speed_slider_y = y_offset + 20  # Align slider with the "Fall Speed" text
                slider_x = right_column_width - 300
                draw_slider(screen, slider_x, fall_speed_slider_y, 0.05, max_fall_speed, fall_speed)
            
            if "Questions Per Level" in text:
                questions_per_level_slider_y = y_offset + 20  # Align slider with the "Questions Per Level" text
                slider_x = right_column_width - 300
                draw_slider(screen, slider_x, questions_per_level_slider_y, 1, max_questions_per_level, questions_per_level)

            if "Lives" in text:
                lives_slider_y = y_offset + 20  # Align slider with the "Lives" text
                slider_x = right_column_width - 300
                draw_slider(screen, slider_x, lives_slider_y, 1, max_lives, lives)

            if "Volume" in text:
                volume_slider_y = y_offset + 20  # Align slider with the "Volume" text
                slider_x = right_column_width - 300
                draw_slider(screen, slider_x, volume_slider_y, 0.0, 1.0, volume)  # Volume slider

            # Check if mouse is over the "Levels Enabled" option and draw a blue box around it
            if "Levels Enabled" in text:
                level_toggle_rect = pygame.Rect(right_x - 5, y_offset, new_font.size(value_text)[0] + 10, 40)
                if level_toggle_rect.collidepoint(pygame.mouse.get_pos()):
                    pygame.draw.rect(screen, BLUE, level_toggle_rect, 2)  # Draw blue box when hovered

            y_offset += 50

        display_text("Use arrow keys to adjust. Press 'Esc' to return", screen_width // 2, screen_height - 50, new_font, WHITE, center=True)
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    settings_running = False
                elif event.key in (pygame.K_UP, pygame.K_DOWN):
                    selected_index = get_next_index(selected_index, 1 if event.key == pygame.K_DOWN else -1)
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    setting = settings[selected_index]
                    var_name = setting["var"]
                    if "toggle" in setting:
                        globals()[var_name] = not globals()[var_name]
                        if var_name == "levels_enabled" and not globals()[var_name]:
                            questions_per_level = -1  # If levels are disabled, set questions_per_level to "infinite" (-1)
                    elif "min" in setting and "max" in setting:
                        step = setting["step"] * (1 if event.key == pygame.K_RIGHT else -1)
                        if var_name == "volume":
                            volume = max(setting["min"], min(setting["max"], volume + step))
                            pygame.mixer.music.set_volume(volume)
                        elif var_name == "fall_speed":
                            fall_speed = max(setting["min"], min(setting["max"], fall_speed + step))
                        elif var_name == "questions_per_level":
                            questions_per_level = round(max(setting["min"], min(setting["max"], questions_per_level + step)))
                        elif var_name == "lives":
                            lives = round(max(setting["min"], min(setting["max"], lives + step)))
        
            # Handle mouse click on sliders to start dragging
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    x, y = pygame.mouse.get_pos()
                    
                    # Check if the click is within any of the slider areas
                    if fall_speed_slider_y - 20 <= y <= fall_speed_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        is_dragging = True
                        fall_speed = (x - slider_x) / 200 * (max_fall_speed - 0.05) + 0.05
                        fall_speed = max(0.05, min(max_fall_speed, fall_speed))  # Clamp the value

                    elif levels_enabled and questions_per_level_slider_y - 20 <= y <= questions_per_level_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        # Only allow interaction with the "Questions Per Level" slider if levels are enabled
                        is_dragging = True
                        questions_per_level = round((x - slider_x) / 200 * (max_questions_per_level - 1) + 1)
                        questions_per_level = max(1, min(max_questions_per_level, questions_per_level))  # Clamp the value

                    elif lives_slider_y - 20 <= y <= lives_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        is_dragging = True
                        lives = round((x - slider_x) / 200 * (max_lives - 1) + 1)
                        lives = max(1, min(max_lives, lives))  # Clamp the value

                    elif volume_slider_y - 20 <= y <= volume_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        is_dragging = True
                        volume = (x - slider_x) / 200 * 1.0  # Scale to the volume range
                        volume = max(0.0, min(1.0, volume))  # Clamp the value
                        pygame.mixer.music.set_volume(volume)

                    # Toggle "Levels Enabled" on click
                    if level_toggle_rect.collidepoint(x, y):
                        levels_enabled = not levels_enabled
                        if not levels_enabled:
                            questions_per_level = -1  # Set questions to "infinite" when levels are disabled

            # Handle mouse drag for sliders
            if event.type == pygame.MOUSEMOTION:
                if is_dragging:
                    x, y = pygame.mouse.get_pos()
                    if fall_speed_slider_y - 20 <= y <= fall_speed_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        fall_speed = (x - slider_x) / 200 * (max_fall_speed - 0.05) + 0.05
                        fall_speed = max(0.05, min(max_fall_speed, fall_speed))  # Clamp the value
                    elif questions_per_level_slider_y - 20 <= y <= questions_per_level_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        questions_per_level = round((x - slider_x) / 200 * (max_questions_per_level - 1) + 1)
                        questions_per_level = max(1, min(max_questions_per_level, questions_per_level))  # Clamp the value
                    elif lives_slider_y - 20 <= y <= lives_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        lives = round((x - slider_x) / 200 * (max_lives - 1) + 1)
                        lives = max(1, min(max_lives, lives))  # Clamp the value
                    elif volume_slider_y - 20 <= y <= volume_slider_y + 20 and slider_x <= x <= slider_x + 200:
                        volume = (x - slider_x) / 200 * 1.0  # Scale to the volume range
                        volume = max(0.0, min(1.0, volume))  # Clamp the value
                        pygame.mixer.music.set_volume(volume)

            # Stop dragging when mouse is released
            if event.type == pygame.MOUSEBUTTONUP:
                is_dragging = False

    new_lives = lives





def start_screen():
    pygame.mixer.music.load(os.path.join(sounds_dir, "start screen music.wav"))
    pygame.mixer.music.play(-1)

    astronaut_background = None
    try:
        astronaut_background_path = os.path.join(images_dir, "Astronaut background.jpg")
        astronaut_background = pygame.image.load(astronaut_background_path)
    except FileNotFoundError:
        print("Astronaut background image not found!")

    while True:
        screen.fill(BLACK)

        if astronaut_background:
            bg_width, bg_height = astronaut_background.get_size()
            bg_x = (screen_width - bg_width) // 2
            bg_y = (screen_height - bg_height) // 2
            screen.blit(astronaut_background, (bg_x, bg_y))

        title_label = fun_font.render("Galactic Recall Quiz Game", True, WHITE)
        screen.blit(title_label, (20, 15))

        start_label = new_font.render("Press 'Enter' to Start", True, WHITE)
        quit_label = new_font.render("Press 'Esc' to Quit", True, WHITE)
        #high_scores_label = new_font.render("Press 'H' for High Scores", True, WHITE) maybe later add high scores
        settings_label = new_font.render("Press 'S' for Settings", True, WHITE)
        
        screen.blit(start_label, (20, 120))
        screen.blit(quit_label, (20, 170))
        screen.blit(settings_label, (20, 220))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    pygame.mixer.music.load(os.path.join(sounds_dir, "Ambiance.wav"))
                    pygame.mixer.music.play()
                    return
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                #elif event.key == pygame.K_h: maybe later add high scores
                    #display_high_scores()
                elif event.key == pygame.K_s:
                    settings_menu()



def display_pause():
    # Scale the background image to fit the screen dynamically
    scaled_bg = pygame.transform.scale(pause_bg, (screen_width, screen_height))
    screen.blit(scaled_bg, (0, 0))  # Draw it at the top-left corner

    # Display text on top of the background
    display_text("Pause", screen_width // 2, screen_height // 4, fun_font, WHITE, center=True)
    display_text("Press 'ESC' to return to the game", screen_width // 2, screen_height - 50, font, WHITE, center=True)
    
    pygame.display.update()
    pygame.mixer.music.stop()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    unpause_sound.play()
                    pygame.mixer.music.load(os.path.join(sounds_dir, "Ambiance.wav"))
                    pygame.mixer.music.play(-1)
                    return
                elif event.key == pygame.K_EQUALS:
                    end_game()


def end_game():
    global score, incorrect_answers, game_over, lives
    game_over = True  # Set the game over flag
    lives = new_lives
    pygame.mixer.music.stop()  # Stop the background music
    explosion_sound.stop()
    win_sound.play()  # Play the win sound

    screen.fill(BLACK)
    screen.blit(pause_bg, (0, 0))  # Draw the background image (pause_bg)
    display_text(f"Game Over! Final Score: {score}", 0, screen_height // 4, score_font, WHITE, center=True)
    display_text("Incorrect Answers:", 0, screen_height // 2 - 50, font, WHITE, center=True)

    y_offset = screen_height // 2
    max_width = screen_width - 100  # Max width for the text
    for i, (question, correct_answer) in enumerate(incorrect_answers):
        color = RED if i % 2 == 0 else DARK_RED
        
        # Prepare the text to display, wrapping it
        incorrect_answer_text = f"{i + 1}. {question} -> {correct_answer}"
        wrapped_lines = wrap_text(incorrect_answer_text, font, max_width)

        # Display the wrapped lines
        for line in wrapped_lines:
            display_text(line, screen_width // 2, y_offset, font, color, center=True)
            y_offset += 40  # Move down for the next line of text

    display_text("Press 'Enter' to Retry", 0, screen_height - 120, font, WHITE, center=True)
    display_text("Press 'Esc' for Main Menu", 0, screen_height - 80, font, WHITE, center=True)
    pygame.display.update()

    # Wait for user input to either retry or go to the main menu
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game_over = False
                    retry_game()
                elif event.key == pygame.K_ESCAPE:
                    start_screen()



def retry_game():
    global score, incorrect_answers, level, questions_answered
    score = 0
    incorrect_answers = []
    level = 1
    questions_answered = 0
    game_loop()

def load_questions():
    global all_questions, unused_questions
    questions = []

    try:
        questions_file_path = os.path.join(base_dir, "Questions.csv")
        with open(questions_file_path, mode="r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            next(csv_reader) 

            for row in csv_reader:
                if len(row) >= 2:  
                    questions.append({"question": row[0], "answer": row[1]})
        
        if not isinstance(questions, list):  
            raise TypeError(f"Expected list, got {type(questions)}")

        all_questions = questions  
        unused_questions = list(all_questions)  
        random.shuffle(unused_questions)  

    except FileNotFoundError:
        print("Error: Questions.csv file not found!")
        return []

    return questions     

def get_user_input(question, y):
    global score, lives, correct_answer, question_text, fall_speed, skipped_question
    input_text = ''
    active = True
    cursor_visible = True
    cursor_timer = 0
    text_fall_position = max(y, 50)

    max_question_width = screen_width * 0.3  # Limit text width to 60% of screen width
    random_offset = random.randint(-200, 200)
    question_x = (screen_width) // 2  # Keep the question centered
    font_size = question_font.size("A")[1]  # Use question_font to get font height
    wrapped_question = wrap_text(question, question_font, max_question_width)  # Wrap text

    incorrect_sound_played = False
    asteroid_reached_bottom = False

    asteroid_rotation_angle = random.randint(0, 360)
    rotation_speed = random.uniform(0.03, 0.05)
    rotation_direction = random.choice([-1, 1])

    while active:
        if background:
            screen.fill(BLACK)
            bg_x = (screen_width - background.get_width()) // 2
            bg_y = (screen_height - background.get_height()) // 2
            screen.blit(background, (bg_x, bg_y))

        # Menu text display
        display_text("Pause", 20, 20, menu_font, WHITE)
        display_text("Quit Game", 20, 60, menu_font, WHITE)
        display_text("Main Menu", 20, 100, menu_font, WHITE)
        display_text("Skip Question", 20, 140, menu_font, WHITE)
        display_text(f"Score: {score}", 20, screen_height - 100, score_font, WHITE)
        display_text(f"Level: {level}", 20, screen_height - 50, score_font, WHITE)
        display_text(f"Lives: {lives}", 20, screen_height - 150, score_font, WHITE)

        # Handle mouse events
        mouse_x, mouse_y = pygame.mouse.get_pos()
        pause_button_rect = pygame.Rect(18, 20, 100, 40)
        quit_button_rect = pygame.Rect(18, 60, 160, 40)
        main_menu_button_rect = pygame.Rect(18, 100, 160, 40)
        skip_question_button_rect = pygame.Rect(18, 140, 240, 40)

        if pause_button_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, BLUE, pause_button_rect, 2)
        if quit_button_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, BLUE, quit_button_rect, 2)
        if main_menu_button_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, BLUE, main_menu_button_rect, 2)
        if skip_question_button_rect.collidepoint(mouse_x, mouse_y):
            pygame.draw.rect(screen, BLUE, skip_question_button_rect, 2)
 

        if text_fall_position < screen_height - 200:
            asteroid_rotation_angle += rotation_speed * rotation_direction
            asteroid_rotation_angle %= 360

            rotated_asteroid = pygame.transform.rotate(asteroid_img, asteroid_rotation_angle)
            asteroid_rect = rotated_asteroid.get_rect(center=(screen_width // 2 + random_offset, text_fall_position))  # Adjust asteroid's x position
            screen.blit(rotated_asteroid, asteroid_rect)

            # Display wrapped and centered question lines with a shadow
            line_height = question_font.get_height()  # Get the line height
            total_text_height = len(wrapped_question) * line_height * 1.25  # Calculate the total height of the wrapped text

            # Adjust the vertical starting position based on the number of lines
            adjusted_y_position = text_fall_position - total_text_height // 2

            shadow_offset = 2  # Offset for the shadow (you can adjust this as needed)

            # Loop to render each line of the wrapped question
            for i, line in enumerate(wrapped_question):
                # Center the line based on its width
                line_width, _ = question_font.size(line)
                centered_x = (screen_width - line_width) // 2  # Center X position

                # Render shadow (black)
                display_text(line, centered_x + random_offset + shadow_offset, adjusted_y_position + (i * line_height * 1.25) + shadow_offset, question_font, BLACK)

                # Render actual text (white)
                display_text(line, centered_x + random_offset, adjusted_y_position + (i * line_height * 1.25), question_font, WHITE)  # Adjust text spacing


        else:
            asteroid_reached_bottom = True

            if not incorrect_sound_played:
                score -= 1
                lives -= 1
                explosion_sound.play()
                incorrect_sound_played = True

                # Only add to incorrect_answers if it's not already there
                if (question_text, correct_answer) not in incorrect_answers:
                    incorrect_answers.append((question_text, correct_answer))

                display_answer()

                

                if lives < 1:
                    end_game()



        asteroid_rotation_angle += rotation_speed * rotation_direction
        asteroid_rotation_angle %= 360

        input_x = (screen_width - font.size(f"Your answer: {input_text}")[0]) // 2
        display_text(f"Your answer: {input_text}", input_x, screen_height - 80, font, WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER]:
                    if input_text.strip().lower() == correct_answer.lower():
                        return input_text.strip()
                    else:                           
                        incorrect_sound.play()
                        score -= 1
                elif event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif len(input_text) < 50:
                    input_text += event.unicode
            if event.type == pygame.MOUSEBUTTONDOWN:
                if pause_button_rect.collidepoint(event.pos):
                    pause_sound.play()
                    display_pause()
                if quit_button_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()
                if main_menu_button_rect.collidepoint(event.pos):
                    start_screen()
                if skip_question_button_rect.collidepoint(event.pos):
                    incorrect_sound.play()
                    score -= 1
                    skipped_question = True
                    display_answer()

        if not asteroid_reached_bottom:
            text_fall_position = min(text_fall_position + (fall_speed), screen_height - 200)

        if cursor_visible:
            cursor_x = input_x + font.size(input_text)[0]
            display_text("|", cursor_x + font.size("a")[0] * 12.5, screen_height - 80, font, WHITE)
        cursor_timer = (cursor_timer + 2) % 750
        cursor_visible = cursor_timer < 325

        pygame.display.update()

        if asteroid_reached_bottom and incorrect_sound_played:
            return input_text.strip()

def display_answer():
    global skipped_question
        # Wrap the question and answer text
    question_text_render = f"Question: {question_text}"
    answer_text_render = f"Correct Answer: {correct_answer}"

    # Wrap the question and answer text
    max_width = screen_width - 40  # Max width for the text
    wrapped_question_lines = wrap_text(question_text_render, question_font, max_width)
    wrapped_answer_lines = wrap_text(answer_text_render, font, max_width)

    # Calculate the initial y_offset for the text
    center_y = screen_height // 2
    y_offset = center_y - (len(wrapped_question_lines) * 20)  # Adjust based on number of lines

    overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Display the wrapped question text
    for line in wrapped_question_lines:
        question_width, question_height = question_font.size(line)
        question_x = (screen_width - question_width) // 2
        display_text(line, question_x, y_offset, question_font, WHITE)
        y_offset += 40  # Move down for the next line

    # Display the wrapped answer text
    for line in wrapped_answer_lines:
        answer_width, answer_height = font.size(line)
        answer_x = (screen_width - answer_width) // 2
        display_text(line, answer_x, y_offset, font, GREEN)
        y_offset += 40  # Move down for the next line

    # Display the "-1 Life" text
    if skipped_question == True:
        display_text("-1 Point", (screen_width // 2) - (font.size("-1 Life")[0] / 2), 20, font, RED)
        skipped_question = False
    else:
        display_text("-1 Life", (screen_width // 2) - (font.size("-1 Life")[0] / 2), 20, font, RED)
    
    pygame.display.update()
    wait_for_input()
        
def game_loop():
    global score, incorrect_answers, level, questions_answered, game_over, used_questions, unused_questions, all_questions, correct_answer, question_text, lives, questions_per_level
    running = True

    # Start background music
    pygame.mixer.music.load(os.path.join(sounds_dir, "Ambiance.wav"))
    pygame.mixer.music.play(-1)

    # Ensure questions are loaded at the start
    if not all_questions:
        all_questions = load_questions()  # Ensure this is a list

    if not isinstance(all_questions, list):  # Check for list type
        raise TypeError(f"all_questions must be a list, but got: {type(all_questions)}")

    # If unused_questions is empty, reload and shuffle
    if not unused_questions:
        unused_questions = list(all_questions)  # Reload questions
        random.shuffle(unused_questions)
        used_questions.clear()  # Clear the used questions


    while running:
        screen.fill(BLACK)

        # Draw background
        if background:
            bg_x = (screen_width - background.get_width()) // 2
            bg_y = (screen_height - background.get_height()) // 2
            screen.blit(background, (bg_x, bg_y))

        pygame.display.update()  # Ensure screen refresh

        # Handle empty question list
        if not unused_questions:
            unused_questions = list(all_questions)  # Reload and shuffle questions
            random.shuffle(unused_questions)
            used_questions.clear()

        # Get the next question
        question_data = unused_questions.pop(0)  # Get the next unused question
        used_questions.append(question_data)  # Add it to used_questions

        if not isinstance(question_data, dict) or "question" not in question_data or "answer" not in question_data:
            raise ValueError(f"Invalid question format: {question_data}")

        question_text = question_data["question"]
        correct_answer = question_data["answer"]


        # Get user input, loop until correct answer
        user_answer = ""
        while user_answer.lower() != correct_answer.lower():
            user_answer = get_user_input(question_text, 100)
        
            if user_answer.lower() == correct_answer.lower():
                score += 1
                correct_sound.play()
                questions_answered += 1

            if questions_answered == questions_per_level and levels_enabled == True:  # to be modified later
                level += 1
                text_surface = score_font.render(f"Level {level} Complete!", True, WHITE)
                text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2))
                box_padding = 20  
                pygame.draw.rect(screen, BLACK, (text_rect.x - box_padding, text_rect.y - box_padding, text_rect.width + 2 * box_padding, text_rect.height + 2 * box_padding))
                screen.blit(text_surface, text_rect)
                pygame.display.update()  
                pygame.time.delay(1500)
                questions_answered = 0

        pygame.display.update()  # Ensure screen refresh




# Start Game
load_background()
start_screen()  # Show the start screen
game_loop()
end_game()