import argparse
from dataclasses import dataclass

import gradio as gr
import pandas as pd
from dotenv import load_dotenv
from langchain import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import DataFrameLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from loguru import logger
from pymongo import MongoClient

load_dotenv()


@dataclass
class Chatbot:
    """
    A Chatbot class that provides a conversational interface for answering user inquiries
    about a specified company. It uses company data stored in MongoDB, chunks and embeds the
    documents for retrieval, and then generates responses using the OpenAI model.

    Args:
        company (str): The company the chatbot is meant to provide information for.
        openai_model (str): The OpenAI model to be used for generating responses. Default is 'gpt-3.5-turbo'.
        openai_temperature (float): The temperature for controlling randomness in the model's output. Default is 0.2.
        embedding_model (str): The model to use for generating text embeddings. Default is 'text-embedding-ada-002'.
        chunk_size (int): The size of each chunk when splitting documents. Default is 1000.
        chunk_overlap (int): The size of the overlap between consecutive chunks. Default is 50.
    """

    company: str
    database: str = "data"
    openai_model: str = "gpt-3.5-turbo"
    openai_temperature: float = 0.2
    embedding_model: str = "text-embedding-ada-002"
    chunk_size: int = 1000
    chunk_overlap: int = 50

    def __post_init__(self):
        self.__connect_mongodb()

    def __connect_mongodb(self) -> None:
        """
        Establishes a connection to MongoDB. The MongoClient instance is connected to the default host
        and port and the `database` attribute is used to specify the database. A collection is
        initialized in the database using the `company` attribute.
        """
        logger.info("Instantiating MongoDB connection...")
        client = MongoClient()
        db = client[self.database]
        self.collection = db[self.company]
        logger.info(f"Instantiated MongoDB connection to collection: {self.company}")

    def get_company_data(self) -> pd.DataFrame:
        """
        Loads the company data from MongoDB, processes it into a DataFrame, and prepares
        it for use with the chatbot.

        Returns
        -------
            pd.DataFrame: A DataFrame containing the company data. Each row represents
            a document, with the columns 'url' and 'text' storing the document's URL and content.
        """
        data = list(self.collection.find())
        df = (
            pd.DataFrame(data)
            .loc[:, ["url", "title", "description", "texts"]]
            .dropna()
            .assign(text=lambda x: "Title: " + x.title + "\nDescription: " + x.description + "\nContent: " + x.texts)
            .loc[:, ["url", "text"]]
        )
        logger.info(f"Number of documents identified for {self.company}: {len(df)}")
        return df

    def run(self) -> None:
        """
        Main function to run the chatbot. This involves the following steps:
        1. Loading the company data.
        2. Splitting the documents into chunks.
        3. Generating embeddings for each chunk.
        4. Initialising the retrieval chain.
        5. Setting up the Gradio interface and launching the chatbot.
        """
        # Load Company Data
        data = self.get_company_data()
        loader = DataFrameLoader(data_frame=data)
        document = loader.load()

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        documents = text_splitter.split_documents(document)
        logger.info(f"Number of documents after splitting: {len(documents)}")

        # Generate embeddings into persistent ChromaDB
        logger.info(f"Generating embeddings using: {self.embedding_model}...")
        embedding = OpenAIEmbeddings(model=self.embedding_model)
        docsearch = Chroma.from_documents(documents=documents, embedding=embedding)

        # Generate custom prompt
        custom_prompt = PromptTemplate.from_template(
            "You are a powerful information giving QA System, your goal is to provide accurate and helpful "
            f"information about the company {self.company}.You should answer user inquiries based on the context "
            f"provided and avoid making up answers.The context comes from the data collected from {self.company} "
            "website.If you don't know the answer, simply state that you don't have enough context to answer it"
            "\nContext:"
            "\n###"
            "\n{context}"
            "\n###"
            "\nQuestion:"
            "\n###"
            "\n{question}"
            "\n###",
        )

        # Initialise Langchain - Conversation Retrieval Chain
        qa = ConversationalRetrievalChain.from_llm(
            ChatOpenAI(temperature=self.openai_temperature, model_name=self.openai_model),
            retriever=docsearch.as_retriever(search_type="similarity", search_kwargs={"k": 6}),
            combine_docs_chain_kwargs=dict(prompt=custom_prompt),
        )

        logger.info("Initializing application...")
        # Setup app
        with gr.Blocks() as app:
            gr.Markdown(f"""<h1><center>{self.company} Chatbot</center></h1>""")
            chatbot = gr.Chatbot(label=f"{self.company} Chatbot", height=900)
            msg = gr.Textbox()
            clear = gr.Button("Clear")
            chat_history = []

            def user(user_message, history):
                # Convert chat history to list of tuples
                chat_history_tuples = []
                for message in chat_history:
                    chat_history_tuples.append((message[0], message[1]))

                # Get response from QA chain
                response = qa({"question": user_message, "chat_history": chat_history_tuples})
                # Append user message and response to chat history
                history.append((user_message, response["answer"]))
                return gr.update(value=""), history

            msg.submit(fn=user, inputs=[msg, chatbot], outputs=[msg, chatbot], queue=False)
            clear.click(fn=lambda: None, inputs=None, outputs=chatbot, queue=False)

        app.launch(debug=True)


if __name__ == "__main__":
    """
    This script initializes the Chatbot with a given company's data and runs the chatbot.
    The company is specified through command line arguments.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("company", help="company to process")
    args = parser.parse_args()

    chatbot = Chatbot(company=args.company)
    chatbot.run()
