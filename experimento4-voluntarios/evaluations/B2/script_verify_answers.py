import pandas as pd
import glob
import os

this_dir = os.path.dirname(os.path.abspath(__file__))

for file in glob.iglob(f"{this_dir}/**/*.csv", recursive=True):

    print(f"Processing file: {file}")
    data = pd.read_csv(file)

    data = data[data["Resposta"].isnull()]

    if data.shape[0] != 0:
        for index, row in data.iterrows():
            print(
                f"ERROR :: Arquivo {file} - Está sem resposta na pergunta {index + 1}"
            )
