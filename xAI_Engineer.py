import os
import requests
import json
import time
import re

def call_grok_api(messages):
    api_key = 'YOUR_XAI_API_KEY'  # Replace with your actual API key
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


def estimate_file_sizes(structure, goal):
    """
    通过调用xAI API来估算项目中每个文件的大小
    
    参数:
    - structure: 项目目录结构
    - goal: 用户的项目目标
    
    返回一个字典，键为文件路径，值为估计大小（带单位）
    """
    system_message = {
        'role': 'system',
        'content': (
            'You are an AI assistant specializing in software project estimation. '
            'Given a project structure and goal, estimate the file sizes in a precise and realistic manner. '
            'Consider the complexity of each file based on its purpose in the project. '
            'Provide estimated sizes with appropriate units (KB, bytes). '
            'Be conservative and factor in typical code complexity. '
            'Return results ONLY as a JSON with file paths and sizes. Example: {"main.py": "2 KB", "utils.py": "1.5 KB"}'
        )
    }
    
    user_message = {
        'role': 'user',
        'content': (
            f'Project Goal: {goal}\n\n'
            f'Project Directory Structure:\n{json.dumps(structure, indent=4)}\n\n'
            'Please estimate file sizes considering the goal and structure. '
            'Include the unit (KB or bytes) for each file. '
            'Ensure the estimates are realistic and proportional to the project complexity. '
            'IMPORTANT: ONLY return a JSON object with file paths as keys and sizes as values.'
        )
    }
    
    messages = [system_message, user_message]
    
    try:
        response = call_grok_api(messages)
        
        # 尝试从响应中提取JSON
        def extract_json(text):
            # 尝试找到JSON块
            json_matches = re.findall(r'```json\n(.*?)```', text, re.DOTALL)
            if json_matches:
                return json_matches[0]
            
            # 尝试找到花括号包裹的JSON
            json_matches = re.findall(r'{[^}]*}', text, re.DOTALL)
            if json_matches:
                return json_matches[0]
            
            return text.strip()
        
        cleaned_response = extract_json(response)
        
        try:
            file_sizes = json.loads(cleaned_response)
            
            # 验证并修正输出格式
            corrected_file_sizes = {}
            for path, size in file_sizes.items():
                # 确保size是字符串，并包含单位
                if not isinstance(size, str):
                    size = f"{size} KB"
                
                # 如果没有单位，默认添加KB
                if not re.search(r'\s*(KB|bytes)', size):
                    size = f"{size} KB"
                
                corrected_file_sizes[path] = size
            
            return corrected_file_sizes
        
        except (json.JSONDecodeError, ValueError):
            # 如果解析失败，回退到默认估算方法
            print("AI file size estimation failed. Using default estimation.")
            return _default_file_size_estimation(structure)
    
    except Exception as e:
        print(f"Error in file size estimation: {e}")
        return _default_file_size_estimation(structure)

def _default_file_size_estimation(structure):
    """
    默认的文件大小估算方法（作为备选）
    """
    sizes = {}
    for name, sub in structure.items():
        if '.' in name:
            ext = os.path.splitext(name)[1].lower()
            if ext == '.py':
                size = '2 KB'
            elif ext in ['.txt', '.md']:
                size = '1 KB'
            else:
                size = '1 KB'
            sizes[name] = size
        else:
            # 目录，递归处理
            sizes.update(_default_file_size_estimation(sub))
    return sizes

def determine_project_structure(goal):
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
            'If the user\'s goal is very simple that you can achieve it with one python script file(smaller than 5KB), the project can just contain one script file. '
	    'Do not contain any folders or files about \"test\". '
            'Please return the directory structure in JSON format, where folders are represented as objects, and files are empty objects. '
            'Do not include any explanations or additional text before or after the JSON. '
            'Only output the pure JSON content. '
            'Here is an example:\n\n'
            '```json\n' + json.dumps(example_structure, indent=4) + '\n```'
        )
    }
    user_message = {
        'role': 'user',
        'content': (
            f'Based on the following goal, please provide the project directory structure. '
            f'Please return the structure in JSON format similar to the example. '
            f'Only output the JSON structure without any additional explanations or text.\n\n'
            f'Goal:\n"{goal}"\n\n'
            'Please enclose the JSON content within triple backticks (```json).'
        )
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    print("AI's response:")
    print(response)
    project_structure = parse_project_structure(response)
    return project_structure

def parse_project_structure(response):
    try:
        json_matches = re.findall(r'```json\n(.*?)```', response, re.DOTALL)
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
    lines = []
    for key, value in structure.items():
        lines.append('    ' * indent + key + ('/' if value else ''))
        if isinstance(value, dict) and value:
            lines.extend(format_structure(value, indent + 1))
    return '\n'.join(lines)


def decompose_goal(goal, project_structure, file_sizes):
    """
    在这里对AI的提示进行强化，让AI在分解子任务时考虑文件大小、目录架构和用户需求。
    """
    example_subtasks = """
Example of a full list of detailed subtasks (for illustration):
1. Create a new file 'game/player.py' and write the Player class.
     - The Player class should include methods for movement (move_left, move_right, jump) and status updates.
     - This script will import `check_collision` from 'utils/helpers.py' to check interactions with obstacles.
     - The Player class should expose `get_position() -> tuple` that returns the current position as a tuple (x, y).
     - The Player class should expose `update_state(action: str)` that updates the player state based on input actions.
     - Dependencies include `check_collision(rect1: tuple, rect2: tuple) -> bool` from 'utils/helpers.py' for collision detection.
2. Create a new file 'game/enemies.py' and write the Enemy class.
     - The Enemy class should include methods for movement patterns, attacking, and state tracking (e.g., is_alive).
     - This script will import `Level` from 'game/level.py' to instantiate a `Level` object and access the `get_platforms` method.
     - The Enemy class should expose `get_state() -> dict` that returns the current state of the enemy.
     - The Enemy class should expose `update_behavior(player_position: tuple)` that updates the behavior based on player position.
     - Dependencies include `get_platforms()` from an instance of `Level` to retrieve platform positions.
3. Create a new file 'game/level.py' and write the Level class.
     - The Level class should define the structure of game levels, including platform positions, obstacles, and boundaries.
     - This script will import `read_file_safe` from 'utils/helpers.py' to load level configurations.
     - The Level class should expose `get_platforms() -> list` that returns a list of platform positions.
     - The Level class should expose `is_position_valid(position: tuple) -> bool` that checks position validity.
     - Dependencies include `read_file_safe(file_path: str) -> dict` from 'utils/helpers.py'.
4. Create a new file 'game/game_manager.py' and write the GameManager class.
     - The GameManager class should handle the game loop, including updates for player, enemies, and levels.
     - This script will import `Player`, `Enemy`, and `Level` classes for managing game components.
     - The GameManager class should expose `start_game()` that initializes and starts the main loop.
     - The GameManager class should expose `end_game()` that handles game termination or restarting.
     - Dependencies include `Player.update_state`, `Enemy.update_behavior`, and `Level.is_position_valid`.
5. Create a new file 'save_system/save_manager.py' and write the SaveManager class.
     - The SaveManager class should handle saving and loading game progress.
     - This script will import `read_file_safe` and `write_file_safe` from 'utils/helpers.py'.
     - The SaveManager class should expose `save_data(data: dict)` that saves game data.
     - The SaveManager class should expose `load_data() -> dict` that loads and returns game data.
     - Dependencies include `read_file_safe` and `write_file_safe` from 'utils/helpers.py'.
6. Create a new file 'utils/helpers.py' and write utility functions.
     - This script should include reusable functions for collision detection and file handling.
     - Implement `check_collision(rect1: tuple, rect2: tuple) -> bool` for collision checks.
     - Implement `read_file_safe(file_path: str) -> dict` for reading JSON data.
     - Implement `write_file_safe(file_path: str, data: dict)` for writing JSON data.
7. Create a temporary file 'main_1.tmp' and write import statements.
     - Import `Player`, `Enemy`, `Level`, and `GameManager` classes.
     - Import necessary utilities from 'utils/helpers.py'.
     - This file will be appended to 'main.py'.
8. Create a temporary file 'main_2.tmp' and write game initialization code.
     - Initialize `GameManager`, `Player`, and `Level` with required parameters.
     - Include code like: `player = Player(start_position=(0, 0))`.
     - Include code like: `level = Level(config_path="levels/level1.json")`.
     - This file will be appended to 'main.py'.
9. Create a temporary file 'main_3.tmp' and write the game loop code.
     - Define the main game loop with `GameManager` updates.
     - Include code like: `game_manager.update(player_input)`.
     - This file will be appended to 'main.py'.
10. Create a temporary file 'main_4.tmp' and write game over logic.
     - Handle game-over events using `GameManager`.
     - Include code like: `if game_manager.is_game_over(): game_manager.end_game()`.
     - This file will be appended to 'main.py'.
11. Append the content of 'main_1.tmp' to 'main.py'.
12. Append the content of 'main_2.tmp' to 'main.py'.
13. Append the content of 'main_3.tmp' to 'main.py'.
14. Append the content of 'main_4.tmp' to 'main.py'.
15. Delete 'main_1.tmp'.
16. Delete 'main_2.tmp'.
17. Delete 'main_3.tmp'.
18. Delete 'main_4.tmp'.
19. Create a new file 'readme.md' and write project documentation.
    - Include setup instructions for installing dependencies
    - Include instructions for running the game
    - Include description of expected game flow and controls
20. Create a new file 'requirements.txt' and write dependencies.
    - List all required Python packages with versions
    - Include pygame and other necessary libraries
21. Create JSON configuration files in 'levels' folder.
    - Create three level files: 'level1.json', 'level2.json', 'level3.json'
    - Required string fields: level_name (level identifier), background (background theme), music_track (background music file name)
    - Required integer fields: time_limit (seconds to complete level)
    - Required array field 'platforms': each platform object must have x, y, width, height as integers
    - Required array field 'obstacles': each obstacle object must have x, y, width, height as integers and type as string
    - Required array field 'enemies': each enemy object must have x, y as integers and type as string
    - Required array field 'collectibles': each collectible must have x, y as integers, type as string, value as integer
    - Required object field 'spawn_point': must have x, y as integers for player starting position
    - Required object field 'exit_point': must have x, y as integers for level completion position
    - The Level class must validate all fields exist and contain valid data types
    - The Level class must validate all coordinates are within the game boundaries
    - The Level class must validate that platform layouts create a completable path
    - Each subsequent level should increase difficulty through platform spacing and enemy count
"""

    system_message = {
        'role': 'system',
        'content': (
            'You are an AI assistant specializing in software development. '
            'Your task is to break down the user\'s goal into a series of subtasks. '
            'Allowed operations: create/write a text file, delete a file, or append content from one file to another. '
            'Do not include tasks that create audio, image, or binary files. '
            'Do not include tasks that are not feasible in a pure text-based environment. '
            'If the goal is simple enough to achieve it with one script file, do not create any other script file. '
            'If one of the script files is estimated to be bigger than 4KB, create temporary files(For example:snake_1.tmp, snake_2.tmp are the temporary file with parts of the code in snake.py). Otherwise, you don\'t need to do so. What\'s more temporary files should not be bigger than 4KB. You can create more temporary files if it is necessary. '
	    'If there is no temporary files, don\'t \"Append\" anything in the tasks. If you want to \"Append\" something, you must say \"Append the content of \'xxx_n.tmp\' to \'xxx.py\'.\"(n is a number and xxx is the name of the script) '
            'When planning tasks, consider three aspects: user requirements (the goal), the directory structure, and the estimated file sizes of each file. '
            'If multiple temporary files need to be combined into one of the script files, please explicitly output the separate subtasks for appending them in order. '
            'No explanations, only list the tasks.\n\n'
            'Here is an example:\n\n' +
            example_subtasks
        )
    }

    user_message = {
    'role': 'user',
    'content': (
        f'Based on the following goal, project directory structure, and estimated file sizes, please provide a detailed plan. '
        f'Only use these operations: create/write file, delete file, append file content. '
        f'No binary, audio, or image creation. All files are text-based.\n\n'
        f'Goal:\n"{goal}"\n\n'
        f'Project Directory Structure:\n{json.dumps(project_structure, indent=4)}\n\n'
        f'Estimated File Sizes (in bytes):\n{json.dumps(file_sizes, indent=4)}\n\n'
        'For some tasks, especially those begin with \"Create\" or \"Write\", provide the main action on the first line, followed by indented details using "-" marks(if it is necessary). '
        'Each task should have implementation details that describe what the file should contain or do.'
    )
    }
    messages = [system_message, user_message]
    response = call_grok_api(messages)
    plan = parse_subtasks(response)
    return plan

def parse_subtasks(response):
    steps = []
    current_task = []
    lines = response.strip().split('\n')
    
    for line in lines:
        if not line.strip():
            continue
            
        # 检查是否是新的主任务（以数字开头或是独立的create/append/delete操作）
        if (re.match(r'^\d+\.', line.lstrip()) or 
            (not current_task and re.search(r'^(Create|Append|Delete)', line.strip(), re.IGNORECASE))):
            # 如果已经收集了之前的任务，添加到步骤中
            if current_task:
                steps.append('\n'.join(current_task))
                current_task = []
            
            # 移除可能存在的行首数字编号
            clean_line = re.sub(r'^\d+\.\s*', '', line.strip())
            current_task.append(clean_line)
        else:
            # 这是子任务/细节行，添加到当前任务
            if current_task:  # 只在有主任务时添加
                stripped_line = line.strip()
                # 如果行以连字符开头或者是纯操作指令，直接添加
                if (stripped_line.startswith('-') or 
                    re.match(r'^(Create|Append|Delete)', stripped_line, re.IGNORECASE)):
                    current_task.append(stripped_line)
                # 否则，如果不是空行且不是独立操作，添加为子任务
                elif stripped_line:
                    current_task.append(f"- {stripped_line}")
    
    # 不要忘记添加最后一个任务
    if current_task:
        steps.append('\n'.join(current_task))
    
    return steps

def build_filename_to_path_mapping(structure, current_path=''):
    mapping = {}
    for name, sub_structure in structure.items():
        sanitized_name = sanitize_filename(name)
        if '.' in name:
            path = os.path.join(current_path, sanitized_name)
            mapping[sanitized_name] = path
        else:
            new_path = os.path.join(current_path, sanitized_name)
            mapping.update(build_filename_to_path_mapping(sub_structure, new_path))
    return mapping

def execute_plan(plan, project_folder, project_structure, filename_to_path, goal, top_level_dir):
    logs = []
    for step in plan:
        logs.extend(execute_step(step, project_folder, project_structure, filename_to_path, goal, top_level_dir))
    return logs

def execute_step(step, project_folder, project_structure, filename_to_path, goal, top_level_dir):
    logs = []
    main_task = step.split('\n')[0]
    print(f"\nExecuting task:\n{main_task}")
    logs.append(f"\nExecuting task:\n{step}")
    print(f"Top level directory: {top_level_dir}")
    logs.append(f"Top level directory: {top_level_dir}")

    # Build existing files context
    existing_files = {}
    for root, dirs, files in os.walk(project_folder):
        for fname in files:
            if fname.endswith('.py') or fname.endswith('.txt') or fname.endswith('.md') or fname.endswith('.tmp'):
                file_path = os.path.join(root, fname)
                rel_path = os.path.relpath(file_path, project_folder)
                if os.path.isfile(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        existing_files[rel_path] = f.read()

    step_lower = main_task.lower()

    # 处理删除操作
    if 'delete' in step_lower:
        filename = extract_filename(main_task, operation='delete')
        if filename:
            # 规范化文件名
            sanitized_filename = sanitize_filename(filename)
            
            # 统一路径分隔符为 '/'
            sanitized_filename = sanitized_filename.replace('\\', '/')
            top_level_dir_normalized = top_level_dir.replace('\\', '/')

            # 移除重复的顶级目录前缀
            if sanitized_filename.startswith(top_level_dir_normalized + '/'):
                sanitized_filename = sanitized_filename[len(top_level_dir_normalized) + 1:]
            
            # 构建完整路径
            full_path = os.path.normpath(os.path.join(project_folder, sanitized_filename))
            
            print(f"Attempting to delete: {full_path}")
            logs.append(f"Attempting to delete: {full_path}")
            
            try:
                if os.path.exists(full_path):
                    os.remove(full_path)
                    logs.append(f"Deleted file: {full_path}")
                    print(f"Deleted file: {full_path}")
                else:
                    logs.append(f"File not found: {full_path}")
                    print(f"File not found: {full_path}")
            except Exception as e:
                logs.append(f"Error deleting file {full_path}: {e}")
                print(f"Error deleting file {full_path}: {e}")
        else:
            logs.append("No filename specified for deletion.")
            print("No filename specified for deletion.")
        
        return logs

    # Handle append operation
    if 'append' in step_lower:
        # We assume format: "Append the content of 'source' to 'destination'"
        # Extract source and destination filenames
        source, destination = extract_append_filenames(main_task)
        # Debug logs
        print(f"Extracted source: {source}, destination: {destination}")
        logs.append(f"Extracted source: {source}, destination: {destination}")
        if source and destination:
            # Normalize paths first
            source_norm = os.path.normpath(source)
            destination_norm = os.path.normpath(destination)

            # Remove top_level_dir prefix if present
            if source_norm.startswith(top_level_dir + os.sep):
                source_norm = source_norm[len(top_level_dir) + len(os.sep):]
            if destination_norm.startswith(top_level_dir + os.sep):
                destination_norm = destination_norm[len(top_level_dir) + len(os.sep):]

            # Now, join with project_folder
            src_path = os.path.join(project_folder, source_norm)
            dst_path = os.path.join(project_folder, destination_norm)

            # Debug log
            print(f"Source path after normalization and stripping: {src_path}")
            print(f"Destination path after normalization and stripping: {dst_path}")
            logs.append(f"Source path after normalization and stripping: {src_path}")
            logs.append(f"Destination path after normalization and stripping: {dst_path}")

            # Check existence
            if os.path.exists(src_path) and os.path.exists(dst_path):
                with open(src_path, 'r', encoding='utf-8') as sf:
                    src_content = sf.read()
                with open(dst_path, 'a', encoding='utf-8') as df:
                    df.write('\n' + src_content)
                logs.append(f"Appended content of {src_path} to {dst_path}")
                print(f"Appended content of {src_path} to {dst_path}")
            else:
                logs.append(f"Source or destination file not found for append: {src_path}, {dst_path}")
                print(f"Source or destination file not found for append: {src_path}, {dst_path}")
        else:
            logs.append("Could not extract source/destination for append operation.")
            print("Could not extract source/destination for append operation.")
        return logs

    # Handle create/write operation (default)
    if any(keyword in step_lower for keyword in ['write', 'create']):
        filename_from_step = extract_filename(main_task, operation='write')
        if filename_from_step:
            filename = filename_from_step
            # 将路径统一为'/'
            filename = filename.replace('\\', '/')
            top_dir_normalized = top_level_dir.replace('\\', '/')

            sanitized_filename = sanitize_filename(filename)
            # 如果在filename_to_path中找不到，说明是新文件，可直接用sanitized_filename作为relative_path
            if sanitized_filename in filename_to_path:
                relative_path = filename_to_path[sanitized_filename]
            else:
                relative_path = sanitized_filename

            # 再次统一relative_path的分隔符为'/'
            relative_path = relative_path.replace('\\', '/')

            # 如果relative_path以top_level_dir开头，则移除
            if relative_path.startswith(top_dir_normalized + '/'):
                relative_path = relative_path[len(top_dir_normalized) + 1:]

            print(f"Relative path for creation: {relative_path}")
            logs.append(f"Relative path for creation: {relative_path}")

            try:
                content = get_content_from_ai(
                    step,
                    filename,
                    relative_path,
                    project_structure,
                    existing_files={},
                    goal=goal
                )
                full_path = os.path.normpath(os.path.join(project_folder, relative_path))
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Wrote content to {full_path}\n")
                logs.append(f"Wrote content to {full_path}\n")
            except Exception as e:
                logs.append(f"Failed to execute step: {e}")
                print(f"Failed to execute step: {e}")
        else:
            logs.append("No filename specified in step.")
            print("No filename specified in step.")
    else:
        # Other steps (if any appear, just log)
        print(f"Unknown Command: {step}")
        logs.append(f"Unknown Command: {step}")

    return logs

def get_content_from_ai(step, filename, file_path, project_structure, existing_files, goal):
    # Get the main task description (first line) and any additional details
    task_lines = step.split('\n')
    main_task = task_lines[0]
    details = '\n'.join(task_lines[1:]) if len(task_lines) > 1 else ""
    
    context = ""
    if existing_files:
        context = "Here are the current files in the project:\n"
        for fname, content in existing_files.items():
            lang = os.path.splitext(fname)[1][1:]
            context += f"\nFilename: {fname}\nContent:\n```{lang}\n{content}\n```\n"

    project_structure_str = json.dumps(project_structure, indent=4)

    system_message = {
        'role': 'system',
        'content': (
            'You are an AI assistant specializing in software development. '
            'You will be provided with a main task and additional implementation details. '
            'Consider all the details when generating the code. '
            'Provide only the pure text code or content for the file. '
            'No explanations, no audio, no binary. Only code in triple backticks.'
        )
    }
    
    user_message = {
        'role': 'user',
        'content': (
            f'Project Goal:\n"{goal}"\n\n'
            f'Project Directory Structure:\n{project_structure_str}\n\n'
            f'You are working on the file: "{file_path}"\n'
            f'Main Task:\n"{main_task}"\n'
            f'Implementation Details:\n{details}\n\n'
            f'{context}\n'
            'Only provide the code or content enclosed in triple backticks.'
        )
    }

    messages = [system_message, user_message]
    response = call_grok_api(messages)
    content = parse_content_from_response(response)
    return content

def parse_content_from_response(response):
    response = response.replace('\r\n', '\n')
    code_blocks = re.findall(r'```(?:\w*\n)?(.*?)```', response, re.DOTALL)
    if code_blocks:
        content = '\n'.join(code_blocks)
    else:
        # If no code blocks, use the entire response
        content = response.strip()
    return content

def extract_filename(step, operation='write'):
    """
    提取文件名，支持单引号和双引号包围的文件名。
    """
    # 对指令进行清理，移除不必要的字符
    step_clean = re.sub(r'[`\*]', '', step)
    
    # 查找两边带单引号或双引号的文件名
    match = re.search(r'["\']([\w./\\]+)["\']', step_clean)
    if match:
        return match.group(1).strip()
    
    # 针对删除操作的特定格式
    if operation == 'delete':
        # 处理类似 "delete file 'X'" 或 "delete 'X'"
        match = re.search(r'delete\s+(?:the\s+)?file\s+[\'"]?([\w./\\]+)[\'"]?', step_clean.lower())
        if match:
            return match.group(1).strip()
        # 处理直接 "delete 'X'"
        match = re.search(r'delete\s+[\'"]?([\w./\\]+)[\'"]?', step_clean.lower())
        if match:
            return match.group(1).strip()
    
    return None


def extract_append_filenames(step):
    """
    假设格式为 "Append the content of 'source' to 'destination'"
    支持单引号和双引号包围的文件名
    """
    # 使用非贪婪匹配来捕捉引号内的内容
    source_match = re.search(r'append\s+(?:the\s+content\s+of\s+)?[\'"]?([\w./\\]+)[\'"]?', step, re.IGNORECASE)
    if source_match:
        source = source_match.group(1).strip('.,;:\'"')
        # 从source_match.end()开始搜索 'to' 后的目标文件名
        rest = step[source_match.end():]
        dest_match = re.search(r'\bto\s+[\'"]?([\w./\\]+)[\'"]?', rest, re.IGNORECASE)
        if dest_match:
            destination = dest_match.group(1).strip('.,;:\'"')
            return source, destination
    return None, None

def sanitize_filename(filename):
    valid_chars = '-_.() /\\abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    sanitized = ''.join(c for c in filename if c in valid_chars)
    sanitized = sanitized.replace(' ', '_')
    return sanitized

def is_non_text_file(filename):
    non_text_extensions = ['wav', 'png', 'mp3', 'jpg', 'jpeg', 'gif', 'bmp', 'mp4', 'avi', 'mov', 'pdf', 'zip', 'exe']
    extension = filename.split('.')[-1].lower()
    return extension in non_text_extensions

def create_project_folder(project_structure):
    if len(project_structure) != 1:
        raise Exception("Project structure must have exactly one top-level directory.")
    top_level_dir = list(project_structure.keys())[0]
    sanitized_name = sanitize_filename(top_level_dir)
    project_folder = os.path.join(os.getcwd(), sanitized_name)
    os.makedirs(project_folder, exist_ok=True)
    print(f"Created project folder at: {project_folder}")
    return project_folder, project_structure[top_level_dir], top_level_dir

def create_directories(base_path, structure):
    for name, sub_structure in structure.items():
        sanitized_name = sanitize_filename(name)
        dir_path = os.path.join(base_path, sanitized_name)
        if '.' in sanitized_name:
            if is_non_text_file(sanitized_name):
                placeholder_filename = f"{sanitized_name}.replacement"
                full_path = os.path.join(base_path, placeholder_filename)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(f"Placeholder for {sanitized_name}")
                print(f"Created placeholder file for non-text file: {full_path}")
            else:
                with open(dir_path, 'w', encoding='utf-8') as f:
                    f.write('')
                print(f"Created file: {dir_path}")
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            if sub_structure:
                create_directories(dir_path, sub_structure)

def main():
    goal = input("Please enter your software development goal:\n")
    print("\nDetermining project directory structure...")
    project_structure = determine_project_structure(goal)
    if not project_structure:
        print("Failed to determine project structure. Exiting.")
        return
    
    print("\nProject Directory Structure:")
    print(json.dumps(project_structure, indent=4))
    
    print("\nEstimating file sizes...")
    file_sizes = estimate_file_sizes(project_structure, goal)
    
    print("Estimated File Sizes:")
    for file, size in file_sizes.items():
        print(f"{file}: {size}")
    
    proceed = input("\nDo these estimated file sizes look reasonable? Proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Please adjust the estimation or project structure.")
        return

    project_folder, adjusted_structure, top_level_dir = create_project_folder(project_structure)
    create_directories(project_folder, adjusted_structure)
    print("\nCreated project directories and placeholder files.")
    filename_to_path = build_filename_to_path_mapping(adjusted_structure)

    print("\nCreating a detailed plan...")
    # 将 file_sizes 传入 decompose_goal，促使AI考虑文件大小
    plan = decompose_goal(goal, project_structure, file_sizes)
    print("\nDetailed Plan:")
    for i, step in enumerate(plan, 1):
        # 分割步骤的多行内容
        lines = step.split('\n')
        # 打印主任务（第一行），移除可能存在的序号
        main_task = re.sub(r'^\d+\.\s*', '', lines[0].strip())
        print(f"{i}. {main_task}")
        # 打印子任务细节（其余行）
        for detail in lines[1:]:
            if detail.strip():
                print(f"   {detail.strip()}")

    proceed = input("\nPlease confirm the above detailed plan is correct. Proceed? (y/n): ")
    if proceed.lower() != 'y':
        print("Operation cancelled.")
        return
    logs = execute_plan(plan, project_folder, adjusted_structure, filename_to_path, goal, top_level_dir)
    print("\nAll steps executed.")
    print("\nExecution logs:")
    for log in logs:
        print(log)
    print(f"\nYour project files are located in: {project_folder}")

if __name__ == "__main__":
    main()
