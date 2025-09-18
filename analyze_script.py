from openai import OpenAI

client = OpenAI(api_key="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")


def analyze_transcript(transcript):
  """
  transcript: list of dicts [{"speaker": "SPEAKER_0", "text": "Hello ..."}, ...]
  """

  # Convert transcript into readable text
  conversation = "\n".join(
    [f"{line['speaker']}: {line['text']}" for line in transcript])

  prompt = f"""
    You are a conversation analyst. Given this transcript:

    {conversation}

    Provide the following:
    1. A summary of the conversation.
    2. Sentiment of each speaker (Positive, Neutral, Negative).
    3. Any actions, commitments, or tasks mentioned.
    """

  response = client.chat.completions.create(
    model="gpt-4o-mini",  # or "gpt-4.1" if you want stronger reasoning
    messages=[
      {"role": "system",
       "content": "You are an expert in analyzing conversations."},
      {"role": "user", "content": prompt}
    ]
  )

  return response.choices[0].message.content


if __name__ == "__main__":
  # Example aligned transcript
  transcript = [
    {"speaker": "Agent", "text": "Hello, how can I help you today?"},
    {"speaker": "Customer", "text": "I’m facing an issue with my payment."},
    {"speaker": "Agent", "text": "I’ll check it for you and get back shortly."}
  ]

  result = analyze_transcript(transcript)
  print(result)
