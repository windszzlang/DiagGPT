if __name__ == '__main__':
    import os
    import threading
    from diaggpt.embedding.embeder import get_vectorstore, Embedder
    from diaggpt.main import DiagGPT


    with open('openai_api_key.txt') as f:
        os.environ['OPENAI_API_KEY'] = f.read()
    # opensearch_url = ''
    # index_name = ''
    # user_index_name = ''
    # user = ''
    # password = ''

    # background_embedder = Embedder(get_vectorstore(opensearch_url, index_name, (user, password)))
    # user_embedder = Embedder(get_vectorstore(opensearch_url, user_index_name, (user, password)))
    # ai_model = DiagGPT(background_embedder)
    ai_model = DiagGPT()
    while True:
        user_input = input('[User] ')
        print('[AI] ', end='')  # default callback let output stream to stdout
        # t = threading.Thread(target=ai_model.run, args=(user_input, user_embedder))
        t = threading.Thread(target=ai_model.run, args=(user_input, None))
        t.start()
        new_token = ai_model.streaming_buffer.get()
        while new_token is not None:
            print(new_token, end='')  # yield new_token in flask
            new_token = ai_model.streaming_buffer.get()
        t.join()
        print()
