import os
import requests
import json
import time
import re

def call_grok_api(messages):
    """
    Calls the Grok-2 API with the given messages.

    Parameters:
        messages (list): A list of message dictionaries for the API.

    Returns:
        str: The content of the response from the Grok-2 model.
    """
    api_key = 'YOUR_API_KEY'  # Replace with your actual API key
    url = 'https://api.x.ai/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    data = {
        'messages': messages,
        'model': 'grok-beta',
        'stream': False,
        'temperature': 0
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        result = response.json()
        return result['choices'][0]['message']['content']
    else:
        raise Exception(f"Error: {response.status_code} - {response.text}")

def determine_project_structure(goal):
    """
    Determines the project directory structure based on the user's goal.

    Parameters:
        goal (str): The user's goal description.

    Returns:
        dict: A dictionary representing the project structure.
    """
    example_structure = {
        "snake_game": {
            "README.md": {},
            "requirements.txt": {},
            "main.py": {},
            "game": {
                "__init__.py": {},
                "snake.py": {},
                "food.py": {},
                "game_manager.py": {}
            },
            "assets": {
                "images": {
                    "snake.png": {},
                    "food.png": {}
                },
                "sounds": {
                    "eat.wav": {},
                    "game_over.wav": {}
                }
            },
            "save_system": {
                "__init__.py": {},
                "save_manager.py": {}
            },
            "utils": {
                "__init__.py": {},
                "helpers.py": {}
            }
        }
    }

    system_message = {
        'role': 'system',
        'content': (
            'You are an AI assistant specializing in software development. '
            'Your task is to provide the project directory structure based on the user\'s goal. '
            'Please return the directory structure in JSON format, where folders are represented as objects, and files are empty objects. '
            'Do not include any explanations or additional text before or after the JSON. '
            'Only output the pure JSON content. '
            'Here is an example:\n\n'
            '```\n' + json.dumps(example_structure, indent=4) + '\n```'
        )
    }
    user_message = {
        'role': 'user',
        'content': (
            f'Based on the following goal, please provide the project directory structure. '
            f'Please return the structure in JSON format similar to the example. '
            f'Only output the JSON structure without any additional explanations or text.\n\n'
            f'Goal:\n"{goal}"\n\n'
            'Please enclose the JSON content within triple backticks (```).'
        )
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    print("AI's response:")
    print(response)
    project_structure = parse_project_structure(response)
    return project_structure

def parse_project_structure(response):
    """
    Parses the project directory structure from the AI's response.

    Parameters:
        response (str): The response from the AI.

    Returns:
        dict: A dictionary representing the project structure.
    """
    try:
        # Extract JSON content between triple backticks
        json_matches = re.findall(r'```(.*?)```', response, re.DOTALL)
        if json_matches:
            json_content = json_matches[0].strip()
            structure = json.loads(json_content)
            return structure
        else:
            print("No JSON content found in AI's response.")
            print("AI's response:")
            print(response)
            return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing project structure: {e}")
        print("AI's response:")
        print(response)
        return {}

def format_structure(structure, indent=0):
    """
    Formats the project structure dictionary into a string.

    Parameters:
        structure (dict): The project directory structure.
        indent (int): Current indentation level.

    Returns:
        str: A formatted string representing the structure.
    """
    lines = []
    for key, value in structure.items():
        lines.append('    ' * indent + key + ('/' if value else ''))
        if isinstance(value, dict) and value:
            lines.extend(format_structure(value, indent + 1))
    return '\n'.join(lines)

def decompose_goal(goal, project_structure):
    """
    Decomposes the user's goal into a detailed plan using the AI model.

    Parameters:
        goal (str): The user's goal description.
        project_structure (dict): The project directory structure.

    Returns:
        list: A list of plan steps extracted from the model's response.
    """
    example_subtasks = """
Example of a full list of detailed subtasks for a snake game with a save system:

Its Project Directory Structure(this is not the part you are going to output):
snake_game/
    README.md
    requirements.txt
    main.py
    game/
        __init__.py
        snake.py
        food.py
        game_manager.py
    assets/
        images/
            snake_head.png
            snake_body.png
            food.png
        sounds/
            eat.wav
            game_over.wav
    save_system/
        __init__.py
        save_manager.py
    utils/
        __init__.py
        helpers.py

Subtasks:(This is what you need to output)
1. Set up the project directory structure as specified above.
2. Initialize a Git repository in the 'snake_game/' directory.
3. Create a virtual environment in 'snake_game/' and install necessary packages like pygame.
4. Write the main game loop in 'snake_game/main.py' that initializes the game window and handles user input and events.
5. Implement the Snake class in 'snake_game/game/snake.py' with methods for movement (`move()`), growth (`grow()`), and collision detection (`check_collision()`), ensuring it interacts with `GameManager` in 'snake_game/game/game_manager.py'.
6. Implement the Food class in 'snake_game/game/food.py' with methods to randomly place food on the game grid (`place_food()`) and detect when the snake consumes it.
7. Implement the GameManager class in 'snake_game/game/game_manager.py' to handle game states (`start_game()`, `pause_game()`, `end_game()`), and manage interactions between `Snake` and `Food` classes.
8. Implement the SaveManager class in 'snake_game/save_system/save_manager.py' for saving and loading game states to a file, including methods like `save_game()` and `load_game()`.
9. Write helper functions in 'snake_game/utils/helpers.py' for tasks like rendering text on the screen and managing high scores.
10. Add sound effects and images to the 'snake_game/assets/' folder and ensure they are correctly loaded and used in the game.
11. Update 'snake_game/README.md' with installation instructions, usage guidelines, and game controls.
12. Write unit tests for key components like `Snake`, `Food`, and `GameManager` classes using a testing framework like unittest, and place them in 'snake_game/tests/'.
13. Clean up code by adding comments, adhering to PEP 8 standards, and removing any unnecessary files.

Please ensure each subtask is concise and fits on a single line.
"""

    system_message = {
        'role': 'system',
        'content': (
            'You are an AI assistant specializing in software development. '
            'Your task is to decompose the user\'s goal into a detailed plan. '
            'For each subtask that involves writing code, provide detailed descriptions of the functionalities to implement, '
            'specify the functions or methods that need to be written, and mention any dependencies on other scripts or modules. '
            'Include the exact file paths as specified in the project directory structure. '
            'Ensure that each subtask is concise and fits on a single line. '
            'Do not split a single subtask into multiple lines.\n\n'
            'Here is an example:\n\n' +
            example_subtasks +
            'Please follow this format closely when providing the plan.'
        )
    }
    user_message = {
        'role': 'user',
        'content': (
            f'Based on the following goal and project directory structure, please provide a detailed plan, including all operations in the project folder. '
            f'For each subtask that involves writing code, include details about what functionalities to implement, which functions or classes to write, '
            f'and specify any dependencies on other scripts or modules if necessary. '
            f'Include the exact file paths as specified in the project directory structure.\n\n'
            f'Goal:\n"{goal}"\n\n'
            f'Project Directory Structure:\n{json.dumps(project_structure, indent=4)}\n\n'
            'Please ensure each subtask is concise and fits on a single line. '
            'Do not split a single subtask into multiple lines.\n\n'
            'Provide the detailed plan in a numbered list.'
        )
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    plan = parse_subtasks(response)
    return plan


def parse_subtasks(response):
    """
    Parses the subtasks or plan steps from the AI's response.

    Parameters:
        response (str): The response from the AI.

    Returns:
        list: A list of parsed steps.
    """
    steps = []
    lines = response.strip().split('\n')
    for line in lines:
        if line.strip():
            # Remove numbering if present
            task = line.strip()
            match = re.match(r'^\d+(\.\d+)*\.?\s*(.*)', task)
            if match:
                task = match.group(2).strip()
            steps.append(task)
    return steps

def build_filename_to_path_mapping(structure, current_path=''):
    """
    Recursively builds a mapping from filenames to their paths in the project structure.

    Parameters:
        structure (dict): The project directory structure.
        current_path (str): The current path in the recursion.

    Returns:
        dict: A mapping from filenames to their paths.
    """
    mapping = {}
    for name, sub_structure in structure.items():
        sanitized_name = sanitize_filename(name)
        if '.' in name:
            # It's a file
            path = os.path.join(current_path, sanitized_name)
            mapping[sanitized_name] = path
        else:
            # It's a directory
            new_path = os.path.join(current_path, sanitized_name)
            mapping.update(build_filename_to_path_mapping(sub_structure, new_path))
    return mapping

def execute_plan(plan, project_folder, project_structure, filename_to_path, goal):
    logs = []
    for step in plan:
        logs.extend(execute_step(step, project_folder, project_structure, filename_to_path, goal))
    return logs

def execute_step(step, project_folder, project_structure, filename_to_path, goal):
    logs = []
    print(f"\nExecuting step: {step}")
    logs.append(f"Executing step: {step}")

    # Build existing files context
    existing_files = {}
    for root, dirs, files in os.walk(project_folder):
        for fname in files:
            if fname.endswith('.py') or fname.endswith('.txt') or fname.endswith('.md'):
                file_path = os.path.join(root, fname)
                rel_path = os.path.relpath(file_path, project_folder)
                if os.path.isfile(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_files[rel_path] = f.read()

    # Determine if we need to get content from AI
    if any(keyword in step.lower() for keyword in ['write', 'implement', 'add', 'update', 'create']):
        filename_from_step = extract_filename(step)
        if filename_from_step:
            filename = filename_from_step
            # Get the correct relative path
            sanitized_filename = sanitize_filename(filename)
            if sanitized_filename in filename_to_path:
                relative_path = filename_to_path[sanitized_filename]
            else:
                relative_path = sanitized_filename
            try:
                content = get_content_from_ai(
                    step,
                    filename,
                    relative_path,
                    project_structure,
                    existing_files,
                    goal
                )
                full_path = os.path.normpath(os.path.join(project_folder, relative_path))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Wrote content to {full_path}")
                logs.append(f"Wrote content to {full_path}")
            except Exception as e:
                logs.append(f"Failed to execute step: {e}")
                print(f"Failed to execute step: {e}")
        else:
            logs.append("No filename specified in step.")
            print("No filename specified in step.")
    else:
        # Other steps
        print(f"Directly executing step: {step}")
        logs.append(f"Executed step directly: {step}")
    return logs

def get_content_from_ai(step, filename, file_path, project_structure, existing_files, goal):
    """
    Gets content from the AI for the given step.

    Parameters:
        step (str): The step description.
        filename (str): The name of the file.
        file_path (str): The path to the file within the project.
        project_structure (dict): The project directory structure.
        existing_files (dict): A dictionary of existing files and their contents.
        goal (str): The user's overall goal.

    Returns:
        str: The content to be written to the file.
    """
    # Prepare the existing files context
    context = ""
    if existing_files:
        context = "Here are the current files in the project:\n"
        for fname, content in existing_files.items():
            context += f"\nFilename: {fname}\nContent:\n```\n{content}\n```\n"

    # Prepare the project directory structure
    project_structure_str = json.dumps(project_structure, indent=4)

    system_message = {
        'role': 'system',
        'content': (
            'You are an AI assistant specializing in software development. '
            'Your task is to provide the code or content for the specified file in the project. '
            'Do not include any explanations. '
            'Only provide the code or content enclosed in triple backticks.'
        )
    }
    user_message = {
        'role': 'user',
        'content': (
            f'Project Goal:\n"{goal}"\n\n'
            f'Project Directory Structure:\n{project_structure_str}\n\n'
            f'You are working on the file: "{file_path}"\n'
            f'Task Description:\n"{step}"\n\n'
            f'{context}\n'
            'Only provide the code or content enclosed in triple backticks.'
        )
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    content = parse_content_from_response(response)
    return content


def parse_content_from_response(response):
    """
    Parses the content from the AI's response.

    Parameters:
        response (str): The response from the AI.

    Returns:
        str: The content extracted from the response.
    """
    # Remove any markdown formatting from the response
    response = response.replace('\r\n', '\n')
    code_blocks = re.findall(r'```(?:\w*\n)?(.*?)```', response, re.DOTALL)
    if code_blocks:
        content = '\n'.join(code_blocks)
    else:
        # If no code blocks, use the entire response
        content = response.strip()
    return content

def extract_filename(step):
    """
    Extracts the filename from the step description.

    Parameters:
        step (str): The step description.

    Returns:
        str: The extracted filename, or None if not found.
    """
    # Remove any markdown or formatting characters
    step_clean = re.sub(r'[`*"]', '', step)
    # Try to match patterns like 'in filename'
    match = re.search(r'\b(?:in|to|into)\s+([\w./\\]+)', step_clean.lower())
    if match:
        filename = match.group(1)
        # Remove any trailing punctuation
        filename = filename.strip('.,;:')
        return filename
    # Try to match 'filename' directly
    match = re.search(r'\b([\w./\\]+\.\w+)', step_clean.lower())
    if match:
        filename = match.group(1)
        filename = filename.strip('.,;:')
        return filename
    return None

def sanitize_filename(filename):
    """
    Sanitizes the filename by removing or replacing invalid characters.

    Parameters:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """
    # Define a whitelist of allowed characters (alphanumeric and some special characters)
    valid_chars = '-_.() /\\abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    sanitized = ''.join(c for c in filename if c in valid_chars)
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    return sanitized

def is_non_text_file(filename):
    """
    Checks if a file is a non-text file based on its extension.

    Parameters:
        filename (str): The filename to check.

    Returns:
        bool: True if it's a non-text file, False otherwise.
    """
    non_text_extensions = ['wav', 'png', 'mp3', 'jpg', 'jpeg', 'gif', 'bmp', 'mp4', 'avi', 'mov', 'pdf', 'zip', 'exe']
    extension = filename.split('.')[-1].lower()
    return extension in non_text_extensions

def create_project_folder(project_structure):
    """
    Creates the project folder using the top-level directory from the project structure.

    Parameters:
        project_structure (dict): The project directory structure.

    Returns:
        tuple: The path to the created project folder and adjusted structure.
    """
    # Get the top-level directory name from the project structure
    if len(project_structure) != 1:
        raise Exception("Project structure must have exactly one top-level directory.")
    top_level_dir = list(project_structure.keys())[0]
    sanitized_name = sanitize_filename(top_level_dir)
    project_folder = os.path.join(os.getcwd(), sanitized_name)
    os.makedirs(project_folder, exist_ok=True)
    print(f"Created project folder at: {project_folder}")
    # Return the project folder path and the adjusted project structure without the top-level directory
    return project_folder, project_structure[top_level_dir]

def create_directories(base_path, structure):
    """
    Recursively creates directories and placeholder files based on the given structure.

    Parameters:
        base_path (str): The base path where directories should be created.
        structure (dict): The nested dictionary representing directory structure.
    """
    for name, sub_structure in structure.items():
        sanitized_name = sanitize_filename(name)
        dir_path = os.path.join(base_path, sanitized_name)
        if '.' in sanitized_name:
            # It's a file
            if is_non_text_file(sanitized_name):
                # Create placeholder for non-text file
                placeholder_filename = f"{sanitized_name}.replacement"
                full_path = os.path.join(base_path, placeholder_filename)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(f"Placeholder for {sanitized_name}")
                print(f"Created placeholder file for non-text file: {full_path}")
            else:
                # Create empty text file
                with open(dir_path, 'w', encoding='utf-8') as f:
                    f.write('')
                print(f"Created file: {dir_path}")
        else:
            # It's a directory
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            if sub_structure:
                create_directories(dir_path, sub_structure)

def main():
    """
    Main function to run the autonomous AI agent.
    """
    # Receive user goal
    goal = input("Please enter your software development goal:\n")
    # Determine project structure
    print("\nDetermining project directory structure...")
    project_structure = determine_project_structure(goal)
    if not project_structure:
        print("Failed to determine project structure. Exiting.")
        return
    # Output project structure for user confirmation
    print("\nProject Directory Structure:")
    print(json.dumps(project_structure, indent=4))
    # Ask user to confirm
    proceed = input("\nPlease confirm the above project directory structure is correct. Proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Operation cancelled.")
        return
    # Create project folder using the top-level directory from the project structure
    project_folder, adjusted_structure = create_project_folder(project_structure)
    # Create directories as per the project structure
    create_directories(project_folder, adjusted_structure)
    print("\nCreated project directories and placeholder files.")
    # Build filename to path mapping
    filename_to_path = build_filename_to_path_mapping(adjusted_structure)
    # Decompose goal into a detailed plan
    print("\nCreating a detailed plan...")
    plan = decompose_goal(goal, project_structure)
    # Output the detailed plan for user confirmation
    print("\nDetailed Plan:")
    for i, step in enumerate(plan):
        print(f"{i+1}. {step}")
    proceed = input("\nPlease confirm the above detailed plan is correct. Proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Operation cancelled.")
        return
    # Execute plan
    logs = execute_plan(plan, project_folder, adjusted_structure, filename_to_path, goal)
    # Provide final result
    print("\nAll steps executed.")
    print("\nExecution logs:")
    for log in logs:
        print(log)
    # Clean up temporary files if any
    # Implement cleanup logic here if needed
    print(f"\nYour project files are located in: {project_folder}")

if __name__ == "__main__":
    main()