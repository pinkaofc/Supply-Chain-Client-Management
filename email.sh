#!/usr/bin/env bash

# Define the base directory
base_dir="email_assistant"

# Create the base directory and subdirectories
mkdir -p "$base_dir"/{agents,core,utils}

# Create Python module files in agents
touch "$base_dir"/agents/__init__.py
touch "$base_dir"/agents/filtering_agent.py
touch "$base_dir"/agents/summarization_agent.py
touch "$base_dir"/agents/response_agent.py
touch "$base_dir"/agents/human_review_agent.py

# Create Python module files in core
touch "$base_dir"/core/__init__.py
touch "$base_dir"/core/email_ingestion.py
touch "$base_dir"/core/email_sender.py
touch "$base_dir"/core/state.py
touch "$base_dir"/core/supervisor.py

# Create Python module files in utils
touch "$base_dir"/utils/__init__.py
touch "$base_dir"/utils/logger.py
touch "$base_dir"/utils/formatter.py

# Create root-level project files
touch "$base_dir"/sample_emails.json
touch "$base_dir"/config.py
touch "$base_dir"/main.py
touch "$base_dir"/requirements.txt
touch "$base_dir"/README.md
touch "$base_dir"/.env

echo "Project structure for '$base_dir' created successfully."