import time
from os import os

from assistant_manager import AssistantManager
from eleven_labs_manager import eleven_labs_manager

assistant_manager = AssistantManager(openai_api_key=os.getenv("OPENAI_API_KEY"))

def interact_with_assistant(transcription):
    global last_thread_id, last_interaction_time
    if not last_thread_id or time.time() - last_interaction_time > 90:
        last_thread_id = assistant_manager.create_thread()

    last_interaction_time = time.time()

    message_id = assistant_manager.add_message_to_thread(last_thread_id, transcription)
    print(f"Message added with ID: {message_id}")
    run_id = assistant_manager.run_assistant(last_thread_id, assistant_id="asst_3D8tACoidstqhbw5JE2Et2st", instructions=transcription)
    print(f"Assistant run initiated with ID: {run_id}")

    run_status = assistant_manager.check_run_status(last_thread_id, run_id)
    if run_status == 'pending':
        assistant_manager.handle_pending_state(run_id)
    elif run_status == 'requires_action':
        functions_to_call = assistant_manager.handle_requires_action_state(run_id)
        for function in functions_to_call:
            result = globals()[function['name']](*function['arguments'])
            assistant_manager.submit_function_results(run_id, result)
    elif run_status == 'queued':
        assistant_manager.handle_queued_state(run_id)
    else:
        print('Run is in an unknown state.')
    if assistant_manager.check_run_status(last_thread_id, run_id):
        response = assistant_manager.retrieve_most_recent_message(last_thread_id)
        processed_response = response.content[0].text.value
        eleven_labs_manager.play_text(processed_response)
        print(f"Played back the assistant's response: {processed_response}")
    else:
        print("Assistant processing failed or timed out.")
