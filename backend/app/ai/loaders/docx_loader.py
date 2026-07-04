from langchain_community.document_loaders import Docx2txtLoader


class DOCXLoaderService:

    def load(self, path: str):

        loader = Docx2txtLoader(path)

        return loader.load()