from langchain_community.document_loaders import PyPDFLoader


class PDFLoaderService:

    def load(self, path: str):

        loader = PyPDFLoader(path)

        return loader.load()