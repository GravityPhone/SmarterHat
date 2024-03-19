import os
import time
from word_detector import setup_keyword_detection, set_message_handler
from audio_recorder import start_recording, stop_recording
from assemblyai_transcriber import AssemblyAITranscriber
from assistant_manager import AssistantManager
from eleven_labs_manager import ElevenLabsManager
import logging
from vision_module import VisionModule
from interactions import interact_with_assistant
import traceback

# Initialize modules with provided API keys
assemblyai_transcriber = AssemblyAITranscriber(api_key=os.getenv("ASSEMBLYAI_API_KEY"))
assistant_manager = AssistantManager(openai_api_key=os.getenv("OPENAI_API_KEY"))
eleven_labs_manager = ElevenLabsManager(api_key=os.getenv("ELEVENLABS_API_KEY"))
vision_module = VisionModule(openai_api_key=os.getenv("OPENAI_API_KEY"))

# State variables
is_recording = False
picture_mode = False
last_thread_id = None
last_interaction_time = None

def handle_detected_words(words):
    global is_recording, picture_mode, last_thread_id, last_interaction_time
    detected_phrase = ' '.join(words).lower().strip()
    print(f"Detected phrase: {detected_phrase}")

    if "computer" in detected_phrase and not is_recording:
        start_recording()
        is_recording = True
        print("Recording started...")
    elif "snapshot" in detected_phrase and is_recording:
        picture_mode = True
        print("Picture mode activated...")
    elif "reply" in detected_phrase and is_recording:
        stop_recording()
        is_recording = False
        print("Recording stopped. Processing...")
        process_recording()

def process_recording():
    global picture_mode, last_thread_id, last_interaction_time
    if not last_thread_id or time.time() - last_interaction_time > 90:
        last_thread_id = assistant_manager.create_thread()
        print(f'Thread created with ID: {last_thread_id}')
    transcription = assemblyai_transcriber.transcribe_audio_file("recorded_audio.wav")
    print(f"Transcription result: '{transcription}'")
    interact_with_assistant(transcription, last_thread_id, last_interaction_time)
    last_interaction_time = time.time()
    print('Interacted with assistant.')

    if picture_mode:
        print('Entering Picture Mode.')
        vision_module.capture_image_async()
        description = vision_module.describe_captured_image(transcription=transcription)
        print('Picture Mode processing done.')
        # If there's a recent thread, send the description to it
        if last_thread_id:
            assistant_manager.add_message_to_thread(last_thread_id, description)
            print(f"Description sent to the most recent thread: {last_thread_id}")
        eleven_labs_manager.play_text(description)
        picture_mode = False
    else:
        print('Interacting with assistant.')
        # Create a thread
        thread_id = assistant_manager.create_thread()
        # Add a message to the thread
        message_id = assistant_manager.add_message_to_thread(thread_id, transcription)
        # Run the assistant on the thread
        run_id = assistant_manager.run_assistant(thread_id, 'asst_3D8tACoidstqhbw5JE2Et2st', transcription)
        print(f'Assistant run initiated with ID: {run_id}')
        # Check the run status
        while True:
            run_status = assistant_manager.check_run_status(thread_id, run_id)
            print(f"Run status at {time.time()}: {run_status}")
            time.sleep(1)
            time.sleep(1)




    run_status = assistant_manager.check_run_status(last_thread_id, run_id)
    if run_status == 'pending':
        response = assistant_manager.handle_pending_state(run_id)
        print(f'API response: {response}')
    elif run_status == 'requires_action':
        functions_to_call = assistant_manager.handle_requires_action_state(run_id)
        print(f'API response: {functions_to_call}')
        for function in functions_to_call: # Assuming each function has a 'name' and list of 'arguments'
            result = globals()[function['name']](*function['arguments'])
            response = assistant_manager.submit_function_results(run_id, result)
            print(f'API response: {response}')
    elif run_status == 'queued':
        response = assistant_manager.handle_queued_state(run_id)
        print(f'API response: {response}')
    else:
        print('Run is in an unknown state.')
    
    # Check the run state and call the corresponding method
    while True:
        run_status = assistant_manager.check_run_status(thread_id, run_id)
        print(f'Run status: {run_status}')
        time.sleep(1)
        if run_status == 'pending':
            response = assistant_manager.handle_pending_state(run_id)
            print(f'API response: {response}')
        elif run_status == 'requires_action':
            functions_to_call = assistant_manager.handle_requires_action_state(run_id)
            print(f'API response: {functions_to_call}')
            for function in functions_to_call: # Assuming each function has a 'name' and list of 'arguments'
                result = globals()[function['name']](*function['arguments'])
                response = assistant_manager.submit_function_results(run_id, result)
                print(f'API response: {response}')
        elif run_status == 'queued':
            response = assistant_manager.handle_queued_state(run_id)
            print(f'API response: {response}')
        else:
            print('Run is in an unknown state.')
        
        if run_status == 'pending' or run_status == 'requires_action' or run_status == 'queued':
            continue
        else:
            break
        response = assistant_manager.retrieve_most_recent_message(last_thread_id)
        print(f'API response: {response}')
        # Assuming response contains a complex structure, extract the actual value
        # This is a placeholder; you will need to adjust the extraction logic based on your actual data structure
        processed_response = response.content[0].text.value
        eleven_labs_manager.play_text(processed_response)
        print(f"Played back the assistant's response: {processed_response}")
    else:
        print("Assistant processing failed or timed out.")



def setup_logging():
 sweep/implement_more_robust_logging_of_main_co_5a999
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the logging level to DEBUG to capture all logs

    # Create a file handler
    handler = logging.FileHandler('program.log')
    handler.setLevel(logging.INFO)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(console_handler)

    logging.basicConfig(filename='program.log', filemode='a', format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)
 main

def initialize():
    setup_logging()
    logging.info("System initializing...")
    set_message_handler(handle_detected_words)
    logging.info('Message handler set.')
    setup_keyword_detection()
    logging.info('Keyword detection setup done.')

if __name__ == "__main__":
    initialize()
    while True:
        time.sleep(1)
