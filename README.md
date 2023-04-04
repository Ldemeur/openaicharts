# Automatic Scientist Project Demo
*In GPT-4's own words:*

This project demonstrates an automatic scientist powered by the GPT-4 language model. The primary goal is to perform data analysis autonomously by executing a series of Python commands. The user is only involved in checking the generated Python code for security reasons before execution.

# Link to example reports
[Here are](./reports/20230404_202938d2d8a762.md) [some example reports](./reports/20230404_192436cf1fbf65.md) [generated](./reports/20230404_20464248efda6b.md) [by the model](./reports/20230404_2130387a296c68.md).

The process starts by asking the user for the input file to analyze. If not provided, the default file 'food-enforcement.json' will be used. The GPT-4 model is then prompted to generate Python code for the analysis. The output from the model is expected to be in JSON format, which allows for a structured and clear communication between the model and the program.

As the analysis progresses, the model receives feedback in the form of error messages or the output of the executed code. This allows GPT-4 to correct itself if it generates an error, thus improving the quality of the analysis. The iterative process continues until the model decides to exit or produces an 'exit' command in the JSON response.

After the analysis is complete, the model is prompted to write a summary of the findings in markdown format. This summary, along with the executed commands and their output, is saved as a report in the 'reports' directory.

The project showcases the potential of GPT-4 in autonomously analyzing data and generating insights. It also highlights how the model can learn from the feedback received during the analysis, improving its performance and output quality.

In summary, this project demonstrates an automatic scientist powered by GPT-4, which is capable of performing data analysis by executing Python commands, learning from feedback, and generating a markdown report with the insights obtained. This demo highlights the potential of language models like GPT-4 in automating data analysis tasks while keeping human intervention minimal for security checks.
