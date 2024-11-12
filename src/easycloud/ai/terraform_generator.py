from openai import OpenAI

SYSTEM_PROMPT = """
You are a terraform developer, with focus on AWS cloud.
When the user requests to create an AWS resource, translate his request to terraform infrastructure as code.
Present all the resources under one file. Format the file like this:
```terraform
<your terraform code here>
```
Also present your remarks to the user, explicitly in this format:
```remarks
<your remarks to the user here>
```
Make sure that your terraform code handles all the dependencies to create the requested resource.
"""



client = OpenAI()


def gen_terraform(request: str):
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": request,
            }
        ],
        model="gpt-4o",
    )

    return chat_completion.choices[0].message.content



if __name__ == "__main__":
    print(gen_terraform("create an S3 bucket that allows public upload of images"))
