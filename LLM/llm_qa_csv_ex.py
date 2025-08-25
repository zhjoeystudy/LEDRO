import os
import time
import random
import csv
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler
import call_llm
import json
import argparse
import pickle

# Class Definition
class QaTester:
    def __init__(self, save_folder, llm_model, has_examples=False, roleplay=False, sbs=False, ca=False):
        self.save_folder = save_folder
        self.llm_model = llm_model

        self.start_text = "You are an analog circuit designer"
        if roleplay:
            self.start_text = "You are an analog circuit design assistant. " + self.start_text
        if sbs:
            self.start_text = self.start_text + "\nLet’s talk about this in a step-by-step way."
        if ca:
            self.start_text = self.start_text + "\nPlease be sure you have the correct answer."

        self.examples = []
        if has_examples:
            self.examples = []

    def get_ans(self, input_text):
        response, _ = call_llm.call_llm(self.llm_model, input_text)
        return response

    def mc_tester(self, qa_filename, write_filename):
        # Build full output file path
        output_file = os.path.join(self.save_folder, write_filename)

        # Load QA JSON
        with open(qa_filename, 'r') as f:
            qa_data = json.load(f)

        # Prepare message history
        messages = []
        question1 = qa_data[0]['netlist']
        question2 = qa_data[0]['prompt']
        messages.append({"role": "system", "content": question1})
        messages.append({"role": "user", "content": question2})

        # Call LLM
        out = self.get_ans(messages)
        messages.append({"role": "assistant", "content": out})

        # Save conversation history
        conversation_path = os.path.join(self.save_folder, "my_variablel3.pkl")
        with open(conversation_path, 'wb') as file:
            pickle.dump(messages, file)

        # Write output
        with open(output_file, 'w') as w:
            w.writelines(out)

        return out  # You can return convid logic later if needed

    def mc_tester1(self, qa_filename, write_filename):
        output_file = os.path.join(self.save_folder, write_filename)

        with open(qa_filename, 'r') as f:
            qa_data = json.load(f)

        messages = []
        question = qa_data[0]['prompt']
        messages.append({"role": "user", "content": question})

        out = self.get_ans(messages)
        messages.append({"role": "assistant", "content": out})

        with open(output_file, 'w') as w:
            w.writelines(out)

# Main Execution
if __name__ == "__main__":
    # Set save folder dynamically
    save_folder = os.path.join(os.getcwd(), "output")

    # Create folder if it doesn't exist
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        print(f"Created output folder: {save_folder}")

    # Model name
    modelname = "ollama/qwen:4b"

    # QA file path (relative or absolute)
    qa_filename = os.path.join("data", "sample-qa-data_i.json")  # assumes data folder exists

    # Initialize tester
    tester = QaTester(save_folder, modelname)

    # Run test
    tester.mc_tester(qa_filename, "qa_output.txt")