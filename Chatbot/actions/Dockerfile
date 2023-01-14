# Extend the official Rasa SDK image
FROM rasa/rasa-sdk:3.2.0
USER root
RUN python3 -m pip install SPARQLWrapper

# Use subdirectory as working directory
WORKDIR /app

#RUN python -m pip install python-dotenv

# Copy actions folder to working directory
COPY ./actions /app/actions

EXPOSE 5055

# By best practices, don't run the code with root user
USER 1001