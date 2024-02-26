"""
A simple fitness app storing exercises with reps and sets
3 databases are used: 1 for the exercises, 1 for routines, 1 for goals
"""

#--- Imports ---#

import sqlite3

from tabulate import tabulate #for viewing if only using terminal


#--- Dictionaries ---#

muscle_group_options = [
    'core', 
    'chest', 
    'shoulders', 
    'legs', 
    'back', 
    'biceps',
    'triceps',
    'cardio'] 


#--- Database creation ---#

db = sqlite3.connect('data/workout_db.db')

cursor = db.cursor()

# Check if the table already exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='program'")
if not cursor.fetchone():
    # Create the table and insert initial data only if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS program (Exercise TEXT PRIMARY KEY, Muscle_Group TEXT,
        Reps INT, Sets INT)
        ''')

    db.commit()


routine_db = sqlite3.connect('data/routine_db.db')

r_cursor = routine_db.cursor()

#--- Helper Functions ---#

def get_valid_integer(prompt):
    """
    Repeatedly prompts for an integer until a valid positive integer is received.

    Args:
        prompt (str): The message to display when prompting for input.

    Returns:
        int: The valid positive integer input.
    """

    while True:
        try:
            value = int(input(prompt))
            if value >= 0:
                return value
            else:
                print("Invalid input. Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a valid integer.")

# Used in view_goal_progress
def get_completed_data_for_routine(routine_name, db):
    """
    Retrieves completed reps for each exercise in the given routine.
    """

    completed_data = {}
    cursor = db.cursor()

    exercise_names = cursor.execute(f"SELECT Exercise FROM {routine_name}").fetchall()
    for exercise in exercise_names:
        completed_reps = get_valid_integer(f"Enter the number of reps completed for {exercise[0]}: ")
        completed_data[exercise[0]] = {'reps': completed_reps}

    return completed_data

# Used in view_goal_progress
def get_goal_data_for_exercises(routine_name, db):
    """
    Retrieves goal data for exercises in the chosen routine from the Goals table.
    """

    goal_data = {}
    cursor = db.cursor()

    cursor.execute("SELECT Exercise, GoalValue FROM Goals WHERE Exercise IN (SELECT Exercise FROM {})".format(routine_name))
    results = cursor.fetchall()
    for exercise, goal_reps in results:
        goal_data[exercise] = goal_reps

    return goal_data

#--- Add Exercise ---#

def add_exercise_category():
    print("\nYou have selected the option to add a new exercise to the database.")

    # Validate exercise name
    while True:
        new_exercise_name = input("Please enter the name of the exercise: ")
        if new_exercise_name.strip():  # Check if name is not empty after removing whitespace
            break
        else:
            print("Invalid name. Please enter a valid exercise name.")

    # Validate muscle group
    while True:
        print("Available muscle groups:\n", *muscle_group_options, sep=", ")
        new_muscle = input("Which muscle group does this exercise target primarily: ").lower()
        if new_muscle.strip():  # Check if group is not empty
            if new_muscle in muscle_group_options:  # Check if valid option
                break
            else:
                print(f"Invalid muscle group. Choose from: {', '.join(muscle_group_options)}")
        else:
            print("Invalid group. Please enter a valid muscle group.")

    try:
        # Get valid reps and sets
        new_reps = get_valid_integer("Please enter the amount of reps: ")
        new_sets = get_valid_integer("Please enter the amount of sets: ")

        # Use a parameterized query to prevent SQL injection
        sql_insert = "INSERT INTO program (Exercise, Muscle_Group, Reps, Sets) VALUES (?, ?, ?, ?)"
        cursor.execute(sql_insert, (new_exercise_name, new_muscle, new_reps, new_sets))
        db.commit()
        print("Exercise added successfully!")

    except (KeyboardInterrupt, ValueError):  # Catch cancellation or invalid input
        print("Operation cancelled or invalid input. Exercise not added.")
        db.rollback()  # Rollback any changes to ensure data integrity

#--- Update Exercise ---#

"""
Planned for future update
Delete and re-add can be utilised for now
"""

#--- View Exercises ---#

def view_exercise_category():
    while True:
        view_menu = input('''\nSelect view options:
            1 - View all exercises in database
            2 - View exercises by muscle group
            0 - Back to menu
            : ''')

        if view_menu not in ['1', '2', '0']:
            print("\nInvalid input. Please select from the available list.")
            continue

        if view_menu == '1':
            # View all exercises
            cursor.execute("SELECT * FROM program")
            exercises = cursor.fetchall()
            print("\nAll Exercises:")
            for exercise in exercises:
                print(f"- Exercise: {exercise[0]}".title())
                print(f"  - Muscle Group: {exercise[1]}".title())
                print(f"  - Reps: {exercise[2]}")
                print(f"  - Sets: {exercise[3]}\n")       

        if view_menu == '2':
            # Get unique muscle groups
            muscle_groups = get_unique_muscle_groups()

            # Display available muscle groups
            print("Available muscle groups:")
            for i, group in enumerate(muscle_groups):
                print(f"{i+1}. {group}")

            # Get user's choice of muscle group
            choice = get_valid_integer("Enter the number of the muscle group you want to view: ")
            selected_group = muscle_groups[choice - 1]

            # Query exercises for the selected muscle group
            sql_select = "SELECT * FROM program WHERE Muscle_Group = ?"
            cursor.execute(sql_select, (selected_group,))
            exercises = cursor.fetchall()

            # Display exercises if any found
            if exercises:
                print(f"\nExercises for muscle group '{selected_group.title()}':")
                for exercise in exercises:
                    print(f"- Exercise: {exercise[0]}".title())
                    print(f"  - Reps: {exercise[2]}")
                    print(f"  - Sets: {exercise[3]}\n")
            else:
                print(f"No exercises found for muscle group '{selected_group}'.")

        if view_menu == '0':
            menu()

def get_unique_muscle_groups():
    cursor.execute("SELECT DISTINCT Muscle_Group FROM program")
    muscle_groups = [result[0] for result in cursor.fetchall()]
    return muscle_groups

#--- Delete Exercise ---#

def delete_exercise_category():
    print("\nYou have selected the option to delete an exercise from the database.")
    delete_exercise = input("\nPlease enter the name of the exercise to be deleted: ")
    
    confirmation = input(f"Are you sure you want to delete '{delete_exercise}'? (y/n): ")
    if confirmation.lower() == 'y':
        # Use a parameterized query to prevent SQL injection
        sql_del = "DELETE FROM program WHERE Exercise = ?"
        cursor.execute(sql_del, (delete_exercise,))
        db.commit()
        print(f"Exercise '{delete_exercise}' has been deleted successfully.")
    else:
        print("Deletion cancelled.")

#--- Create Workout Routine ---#
# A new table should be created for every routine
def create_workout_routine():
    """
    Creates a new table for a workout routine in the routine_db database,
    prompts the user to add exercises from the workout_db's program table,
    and inserts the chosen exercises into the routine table.
    """

    while True:
        routine_name = input("Enter a name for the routine (leave blank to generate automatically): ")

        # Allow blank name but generate one if user leaves it empty
        if not routine_name:
            routine_name = f"Routine_{len(r_cursor.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()) + 1}"
            print(f"No name provided, automatically generated name: {routine_name}")
            break

        # Validate entered name for special characters or spaces
        if not routine_name.isalnum():
            print("Invalid routine name. Please use alphanumeric characters only.")
            continue

        break

    table_name = routine_name.replace(" ", "_")  # Sanitize table name

    # Create the routine table
    r_cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            Exercise TEXT,
            Muscle_Group TEXT,
            Reps INT,
            Sets INT
        )
    ''')
    routine_db.commit()

    # Display exercises from the program table with details
    cursor.execute("SELECT * FROM program")
    exercises = cursor.fetchall()
    print("Available exercises:")
    for exercise_data in exercises:
        exercise, muscle_group, reps, sets = exercise_data
        print(f"\t- {exercise} ({muscle_group}) - Reps: {reps}, Sets: {sets}")

    while True:
        exercise_to_add = input("Enter an exercise to add (or 'done' to finish): ")
        if exercise_to_add.lower() == 'done':
            break

        # Check if exercise exists in the program table
        cursor.execute("SELECT * FROM program WHERE LOWER(Exercise) = ?", (exercise_to_add.lower(),))
        exercise_data = cursor.fetchone()
        if exercise_data:
            # Insert exercise details into the routine table
            r_cursor.execute(f'''
                INSERT INTO {table_name} (Exercise, Muscle_Group, Reps, Sets)
                VALUES (?, ?, ?, ?)
            ''', exercise_data)
            routine_db.commit()
            print(f"Exercise '{exercise_to_add}' added to the routine.")
        else:
            print(f"Exercise '{exercise_to_add}' not found in the program database.")

#--- View Workout Routine ---#

def view_workout_routine():
    """
    Displays a list of available workout routines (tables) in the routine_db database,
    prompts the user to choose one, and displays its contents in a formatted table.
    Using a formatted table for when user only uses terminal.
    """

    # Query to fetch table names from the sqlite_master table
    r_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")

    # Retrieve and print the table names
    tables = r_cursor.fetchall()
    print("Workout routines in the database:")
    for i, table in enumerate(tables):
        print(f"{i+1}. {table[0]}")

    # Ask the user to choose a routine
    while True:
        choice = get_valid_integer("Enter the number of the routine you want to view (or 0 to exit): ")
        if choice == 0:
            break
        elif 1 <= choice <= len(tables):
            table_name = tables[choice-1][0]
            break
        else:
            print("Invalid choice. Please enter a number between 1 and", len(tables))

    # Fetch and print the contents of the chosen routine
    if choice != 0:
        r_cursor.execute(f"SELECT * FROM {table_name}")
        rows = r_cursor.fetchall()
        if rows:
            column_names = [desc[0] for desc in r_cursor.description]
            # Use tabulate for formatting
            table = tabulate(rows, headers=column_names, tablefmt="grid")
            print("\nContents of", table_name, "routine:")
            print(table)
        else:
            print("Routine", table_name, "is empty.")

#--- Delete Workout Routine ---#
# Separate db so that user cannot accidentally delete tables in the other databases
def delete_workout_routine(cursor):
    """
    Deletes a workout routine from the routine_db database.
    """

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = cursor.fetchall()

    print("Workout routines in the database:")
    for i, table in enumerate(tables):
        print(f"{i+1}. {table[0]}")

    while True:
        choice = get_valid_integer("Enter the number of the routine you want to delete (or 0 to exit): ")
        if choice == 0:
            break
        elif 1 <= choice <= len(tables):
            table_name = tables[choice-1][0]
            confirmation = input(f"Are you sure you want to delete the routine '{table_name}'? (y/n): ")
            if confirmation.lower() == 'y':
                cursor.execute(f"DROP TABLE {table_name}")
                routine_db.commit()
                print(f"Routine '{table_name}' deleted successfully.")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and", len(tables))

#--- View Exercise Progress ---#

def view_exercise_progress():
    """
    Prompts the user for a routine, retrieves progress data, and displays remaining sets/reps and percentage completion.
    """

    try:
        with sqlite3.connect('data/routine_db.db') as r_db:
            r_db_cur = r_db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            routines = r_db_cur.fetchall()

            # Check if any routines exist
            if routines:
                print("\nAvailable routines:")
                for i, routine in enumerate(routines):
                    print(f"{i+1}. {routine[0]}")

                # Get user choice
                while True:
                    try:
                        choice = get_valid_integer("Enter the number of the routine you want to view progress for (or 0 to exit): ")
                        if choice == 0:
                            break
                        elif 1 <= choice <= len(routines):
                            routine_name = routines[choice-1][0]
                            break
                        else:
                            print("Invalid choice. Please enter a number between 1 and", len(routines))
                    except ValueError:
                        print("Invalid input. Please enter a number.")

            # Initialize completed_data dictionary
            completed_data = {}

            # Get completed reps for each exercise
            exercise_names = r_db.execute(f"SELECT Exercise FROM {routine_name}").fetchall()
            for exercise in exercise_names:
                completed_reps = get_valid_integer(f"Enter the number of reps completed for {exercise[0]}: ")
                completed_data[exercise[0]] = {'reps': completed_reps}

            # Retrieve total sets/reps for each exercise
            total_data = {}
            for exercise, data in completed_data.items():
                total_sets = r_db.execute(f"SELECT MAX(Sets) FROM {routine_name} WHERE Exercise = ?", (exercise,)).fetchone()[0]
                total_reps = r_db.execute(f"SELECT MAX(Reps) FROM {routine_name} WHERE Exercise = ?", (exercise,)).fetchone()[0]
                total_data[exercise] = {'sets': total_sets, 'reps': total_reps}

            # Calculate remaining sets/reps and percentage completion based on reps
            for exercise, completed in completed_data.items():
                total = total_data[exercise]
                remaining_reps = total['reps'] - completed['reps']
                remaining_sets = int(remaining_reps / total['reps'] * total['sets']) + 1 if remaining_reps % total['reps'] > 0 else 0
                completion_percentage = round((completed['reps'] / total['reps']) * 100, 2)

                print(f"\n- {exercise}:")
                print(f"  - Completed: {completed['reps']} reps")
                print(f"  - Remaining: {remaining_sets} sets, {remaining_reps} reps")
                print(f"  - Percentage completion: {completion_percentage}%")

            # Calculate and display overall workout progress
            total_exercises = len(completed_data)
            total_completion = 0
            for exercise, completion in completed_data.items():
                # Ensure valid total data exists for the exercise
                if exercise in total_data:
                    total_completion += (completion['reps'] / (total_data[exercise]['sets'] * total_data[exercise]['reps']))
                else:
                    print(f"Warning: Missing total data for exercise {exercise}. Skipping in overall progress calculation.")

            if total_exercises > 0:  # Avoid division by zero
                overall_completion = round(total_completion / total_exercises * 100, 2)
                print("\nOverall Workout Progress:")
                print(f"- Completed: {overall_completion:.2f}%")
            else:
                print("\nNo exercises completed. Overall progress unavailable.")

    except sqlite3.Error as error:
        print("Error occurred:", error)

#--- Set Fitness Goals ---#

def set_fitness_goals(overwrite_existing=False):
    """
    Prompts the user to set or update fitness goals for saved exercises and saves/updates them to the database.

    Handles overwriting existing goals if desired and provides clear explanations and error handling.

    Args:
        overwrite_existing (bool, optional): Whether to overwrite existing goals for the same exercise. Defaults to False.
    
    Only the latest exercise goal will be saved

    Returns:
        None
    """

    try:
        # Database connections
        workout_db = sqlite3.connect('data/workout_db.db')
        w_cursor = workout_db.cursor()

        goals_db = sqlite3.connect('data/goals.db')
        g_cursor = goals_db.cursor()

        # Create Goals table if it doesn't exist
        try:
            g_cursor.execute('''
                CREATE TABLE IF NOT EXISTS goals (
                    Exercise TEXT PRIMARY KEY,
                    GoalType TEXT,
                    GoalValue INT
                )
            ''')
        except sqlite3.OperationalError as e:
            print(f"Error creating table: {e}")
            return

        # Retrieve available exercises from the "program" table
        available_exercises = []
        try:
            w_cursor.execute("SELECT Exercise FROM program")
            exercises = w_cursor.fetchall()
            for exercise in exercises:
                available_exercises.append(exercise[0])
        except sqlite3.Error as e:
            print(f"Error retrieving exercises: {e}")
            return

        # Loop to set/update goals for multiple exercises
        while True:
            # Show list of available exercises
            print("\nAvailable exercises:")
            for i, exercise in enumerate(available_exercises):
                print(f"{i+1}. {exercise}")

            # Get exercise choice
            try:
                choice = get_valid_integer("Enter the number of the exercise you want to set/update a goal for (or 0 to finish): ")
            except ValueError as e:
                print(f"Invalid input: {e}")
                continue

            if choice == 0:
                break

            # Ensure valid exercise choice
            if 1 <= choice <= len(available_exercises):
                selected_exercise = available_exercises[choice-1]

                # Check for existing goal and handle overwrite option
                existing_goal = g_cursor.execute("SELECT GoalType, GoalValue FROM Goals WHERE Exercise = ?", (selected_exercise,)).fetchone()

                # Display existing goal if found
                if existing_goal:
                    goal_type, goal_value = existing_goal
                    print(f"Existing goal for {selected_exercise}: {goal_type.title()} : {goal_value}")

                if overwrite_existing or not existing_goal:
                    # Set or update goal (no overwrite confirmation needed)
                    goal_reps = get_valid_integer(f"Enter your new total rep goal for {selected_exercise} (or 0 to skip setting a goal): ")
                    if goal_reps > 0:
                        if existing_goal:
                            # Update existing goal
                            try:
                                g_cursor.execute("UPDATE Goals SET GoalValue = ? WHERE Exercise = ?", (goal_reps, selected_exercise))
                                goals_db.commit()
                                print(f"Goal updated successfully for {selected_exercise}: {goal_reps} reps!")
                            except sqlite3.IntegrityError as e:
                                print(f"Error saving goal: {e}")
                            except Exception as e:
                                print(f"An unexpected error occurred: {e}")
                        else:
                            # Insert new goal
                            try:
                                g_cursor.execute("INSERT INTO Goals (Exercise, GoalType, GoalValue) VALUES (?, ?, ?)", (selected_exercise, "reps", goal_reps))
                                goals_db.commit()
                                print(f"Goal set successfully for {selected_exercise}: {goal_reps} reps!")
                            except sqlite3.IntegrityError as e:
                                print(f"Error saving goal: {e}")
                            except Exception as e:
                                print(f"An unexpected error occurred: {e}")

                else:
                    # Existing goal and overwrite not allowed
                    print(f"An existing goal for {selected_exercise} is already set.")
                    if not overwrite_existing:
                        print("Use the `set_fitness_goals(overwrite_existing=True)` call to overwrite existing goals.")

            else:
                print("Invalid choice. Please choose an existing exercise.")

            # Ask if the user wants to set/update goals for more exercises
            more_goals = input("Do you want to set/update goals for other exercises? (y/n): ")
            if more_goals.lower() != 'y':
                break

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        # Close database connections even if errors occur
        workout_db.close()
        goals_db.close()

#--- Delete Fitness Goals ---#

def delete_fitness_goals():
  """Displays current fitness goals and allows user to delete them."""

  try:
    # Database connection
    goals_db = sqlite3.connect('data/goals.db')
    g_cursor = goals_db.cursor()

    # Retrieve existing goals
    try:
      g_cursor.execute("SELECT Exercise, GoalType, GoalValue FROM Goals")
      goals = g_cursor.fetchall()
    except Exception as e:
      print(f"Error retrieving goals: {e}")
      return

    # Check if any goals exist
    if not goals:
      print("No fitness goals found.")
      return

    # Display numbered list of goals
    print("\nYour current fitness goals:")
    for i, (exercise, goal_type, goal_value) in enumerate(goals):
      print(f"{i+1}. {exercise} - {goal_type}: {goal_value}")

    # Get user input
    choice = get_valid_integer("Enter the number of the goal you want to delete (or 0 to quit): ")

    if choice == 0:
      return

    # Ensure valid goal choice
    if 1 <= choice <= len(goals):
      selected_goal = goals[choice-1]

      # Confirm deletion
      confirmation = input(f"Are you sure you want to delete the goal for {selected_goal[0]} - {selected_goal[1]}: {selected_goal[2]} (y/n): ")

      if confirmation.lower() == 'y':
        try:
          # Delete goal from database
          g_cursor.execute("DELETE FROM Goals WHERE Exercise = ? AND GoalType = ? AND GoalValue = ?", selected_goal)
          goals_db.commit()
          print("Goal deleted successfully!")
        except Exception as e:
          print(f"Error deleting goal: {e}")
    else:
      print("Invalid choice. Please choose an existing goal.")

  except Exception as e:
    print(f"An unexpected error occurred: {e}")

  finally:
    # Close database connection
    goals_db.close()

#--- View Progress towards Goal ---#

def view_goal_progress():
    """
    Prompts the user for a specific exercise and displays progress towards its goal.
    Ideal for Calisthenics or other bodyweight associated exercises
    """

    try:
        # Database connections
        workout_db = sqlite3.connect('data/workout_db.db')
        w_cursor = workout_db.cursor()

        goals_db = sqlite3.connect('data/goals.db')
        g_cursor = goals_db.cursor()

        # Retrieve available exercises
        exercises = w_cursor.execute("SELECT Exercise FROM program").fetchall()

        # Check if any exercises exist
        if exercises:
            print("\nAvailable exercises:")
            for i, exercise in enumerate(exercises):
                print(f"{i+1}. {exercise[0]}")

            # Get user choice
            while True:
                try:
                    choice = get_valid_integer("Enter the number of the exercise you want to view progress for (or 0 to exit): ")
                except ValueError:
                    print("Invalid input. Please enter a number.")
                    continue

                if choice == 0:
                    return

                elif 1 <= choice <= len(exercises):
                    selected_exercise = exercises[choice-1][0]
                    break

                else:
                    print("Invalid choice. Please enter a number between 1 and", len(exercises))

            # Check if goal exists for the exercise
            goal_data = g_cursor.execute("SELECT GoalType, GoalValue FROM Goals WHERE Exercise = ?", (selected_exercise,)).fetchone()

            # Display progress if goal exists
            if goal_data:
                goal_type, goal_value = goal_data
                completed_reps = get_valid_integer(f"Enter the number of reps completed for {selected_exercise}: ")
                remaining_reps = goal_value - completed_reps
                completion_percentage = round((completed_reps / goal_value) * 100, 2)

                # Display goal information before progress
                print(f"\n--- Goal for {selected_exercise}:")
                print(f"- Goal type: {goal_type}")
                print(f"- Goal value: {goal_value}")

                print(f"\n- Progress:")
                print(f"  - Completed reps: {completed_reps}")
                print(f"  - Remaining reps: {remaining_reps}")
                print(f"  - Completion percentage: {completion_percentage}%")

            else:
                print(f"\n--- No goal set for {selected_exercise}.")

        else:
            print("\nNo exercises found. Please create exercises first.")

    except sqlite3.Error as error:
        print("Error occurred:", error)

#--- Menu ---#

def menu():
    while True:
        menu = input('''\nSelect one of the following options:
        1 - Add exercise
        2 - View exercise
        3 - Delete exercise
        4 - Create Workout Routine
        5 - View Workout Routines
        6 - Delete Workout Routine
        7 - View Exercise Progress
        8 - Set Fitness Goals
        9 - View Progress towards Fitness Goals
        10 - Delete Fitness Goals
        0 - Quit
        : ''')

        if menu not in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '0', ]:
            print("\nInvalid input. Please select from the available list.")
            continue

        if menu == '1':
            add_exercise_category()

        if menu == '2':
            view_exercise_category()

        if menu == '3':
            delete_exercise_category()

        if menu == '4':
            create_workout_routine()

        if menu == '5':
            view_workout_routine()

        if menu == '6':
            try:
                with sqlite3.connect('data/routine_db.db') as routine_db:
                    r_cursor = routine_db.cursor()
                    delete_workout_routine(r_cursor)  # Pass the cursor to the function
            except sqlite3.Error as e:
                print(f"An error occurred while accessing the database: {e}")

        if menu == '7':
            view_exercise_progress()

        if menu == '8':
            set_fitness_goals(overwrite_existing=True)

        if menu == '9':
            view_goal_progress()

        if menu == '10':
            delete_fitness_goals()

        if menu == '0':
            print('\nGoodluck with your fitness journey. Until next time!')
            exit()

menu()