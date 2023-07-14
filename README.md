# Summary Backend

This project is designed to generate summaries using the `fireballoon/baichuan-vicuna-chinese-7b-gptq` model. It runs locally on your own machine and manages dependencies using `pipenv`.

## Installation

Before running this project, make sure you have `pipenv` installed. Then, use the following command to install the dependencies required for the project:

This will install all the necessary dependencies based on the `Pipfile` in the project.
```
pipenv install
```

## Configuration

Before using the tool, you need to fill in the `API_KEY` variable in the `config.ini` file. Place your OpenAI API key in this variable.

## Usage

The project provides two APIs for generating summaries.

### 1. /summary API

This API generates answers gradually using EventSource and progressively returns the summary.

- **URL**: `<host>/summary`
- **HTTP Method**: POST
- **Payload**: `{"content": "string"}`

### 2. /summary/gpt API

This API uses the GPT API to send the article to the `gpt-3.5-turbo-16k` model and generate a summary.

- **URL**: `<host>/summary/gpt`
- **HTTP Method**: POST
- **Payload**: `{"content": "string"}`

Please use the provided URL, HTTP method, and payload to make the respective API calls for summary generation.

## Additional Notes

- Make sure you have installed the necessary dependencies on your machine and filled in the correct API key.
