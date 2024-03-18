import openai
import time
from vision_module import VisionModule
from interactions import interact_with_assistant
from eleven_labs_manager import ElevenLabsManager

class AssistantManager:
    def __init__(self, openai_api_key):
        openai.api_key = openai_api_key
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

            # Handle 'pending' and 'requires_action' states
            self.handle_pending_state(run.id)
            self.handle_requires_action_state(run.id)

            return run.id
        except Exception as e:
            print(f"Failed to run assistant on thread {thread_id}: {e}")
            return None

    def handle_pending_state(self, run_id):
        vision_module = VisionModule(self.openai_api_key)
        description = vision_module.describe_captured_image(transcription=run_id)
        # Submit the description to the OpenAI Assistant API
        self.client.beta.threads.runs.update(run_id, description=description)

    def handle_requires_action_state(self, run_id):
        pass  # Placeholder - Replace with implementation code

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
                # Handle 'queued' state
                if run_status.status == 'queued':
                    self.handle_queued_state(run_id)
                if run_status.status == 'completed':
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
            return None
