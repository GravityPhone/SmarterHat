import openai
import time
from vision_module import VisionModule

from eleven_labs_manager import ElevenLabsManager

class AssistantManager:
    def __init__(self, openai_api_key):
        self.openai_api_key = openai_api_key
        openai.api_key = self.openai_api_key
        self.client = openai

    def create_thread(self):
        try:
            thread = self.client.beta.threads.create()
            return thread.id
        except Exception as e:
            print(f"Failed to create a thread: {e}")
            return None

    def add_message_to_thread(self, thread_id, message_content, role="user"):
        try:
            message = self.client.beta.threads.messages.create(
                thread_id=thread_id,
                role=role,
                content=message_content
            )
            return message.id
        except Exception as e:
            print(f"Failed to add message to thread {thread_id}: {e}")
            return None

    def run_assistant(self, thread_id, assistant_id, instructions):
        try:
            run = self.client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant_id,
                instructions=instructions
            )
            print('Assistant run created.')

            # Handle 'pending' and 'requires_action' states
            self.handle_pending_state(run.id)
            self.handle_requires_action_state(run.id)

            return run.id
        except Exception as e:
            print(f"Failed to run assistant on thread {thread_id}: {e}")
            return None

    def handle_pending_state(self, run_id):
        vision_module = VisionModule(self.client.api_key)
        description = vision_module.describe_captured_image(transcription=run_id)
        # Submit the description to the OpenAI Assistant API
        self.client.beta.threads.runs.update(run_id, description=description)
        print('Handled pending state.')

    def handle_requires_action_state(self, run_id):
        print('Requires action.')

    def handle_queued_state(self, run_id):
        labs_manager = ElevenLabsManager()
        response_text = self.client.assistant.retrieve(run_id).responses[0]['content']['text']['value'].strip()
        labs_manager.play_text(response_text)
        # End of function handle_queued_state    def check_run_status(self, thread_id, run_id, timeout=300):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run_id
                )
                print(f"Run status at {time.time()}: {run_status.status}")
                # Handle 'queued' state
                if run_status.status == 'queued':
                    self.handle_queued_state(run_id)
                if run_status.status == 'completed':
                    assistant_messages = self.client.beta.threads.messages.list(thread_id=thread_id)
                    print(f'Assistant messages: {assistant_messages}')
                    return True
                elif run_status.status in ['failed', 'cancelled']:
                    return False
                time.sleep(1)
            except Exception as e:
                print(f"Failed to check run status: {e}")
                return False
        return False

    def retrieve_most_recent_message(self, thread_id):
        try:
            response = self.client.beta.threads.messages.list(thread_id=thread_id, order='desc', limit=1)
            # Assuming response.data contains the messages and taking the first one
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Failed to retrieve the most recent message from thread {thread_id}: {e}")
            return None

    def interact_with_assistant(self, transcription):
        global last_thread_id, last_interaction_time
        if not last_thread_id or time.time() - last_interaction_time > 90:
            last_thread_id = self.create_thread()

        last_interaction_time = time.time()

        message_id = self.add_message_to_thread(last_thread_id, transcription)
        print(f"Message added with ID: {message_id}")
        run_id = self.run_assistant(last_thread_id, assistant_id="asst_3D8tACoidstqhbw5JE2Et2st", instructions=transcription)
        print(f"Assistant run initiated with ID: {run_id}")

        run_status = self.check_run_status(last_thread_id, run_id)
        if run_status == 'pending':
            self.handle_pending_state(run_id)
        elif run_status == 'requires_action':
            functions_to_call = self.handle_requires_action_state(run_id)
            for function in functions_to_call:
                result = globals()[function['name']](*function['arguments'])
                self.submit_function_results(run_id, result)
        elif run_status == 'queued':
            self.handle_queued_state(run_id)
        else:
            print('Run is in an unknown state.')
        if self.check_run_status(last_thread_id, run_id):
            response = self.retrieve_most_recent_message(last_thread_id)
            processed_response = response.content[0].text.value
            eleven_labs_manager.play_text(processed_response)
            print(f"Played back the assistant's response: {processed_response}")
        else:
            print("Assistant processing failed or timed out.")
            return None
