#IMPORTANDO LIBRERIAS NECESARIAS
import pandas as pd 
from fastapi import FastAPI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

df_steam = pd.read_csv('./data/steam_games.csv')

df_steam['price'] = df_steam['price'].apply(lambda x: float(x.replace('$', '').replace(',', '')) if isinstance(x, str) 
                                            and x.replace('$', '').replace(',', '').replace('.', '').isdigit() else 0.0)

app = FastAPI()

@app.get('/userdata/{user_id}')
async def userdata(user_id: str):
    try:
        Cantidad = 0
        recommend_count = 0
        total_reviews = 0
        item_ids = set()

        chunk_size = 100000
        user_reviews_generator = pd.read_csv('./data/reviews.csv', chunksize= chunk_size)

        for chunk in user_reviews_generator:
            user_reviews = chunk[chunk['user_id']== user_id] 

            Cantidad += user_reviews.merge(df_steam[['id','price']], left_on='item_id', right_on='id', how='inner')['price'].sum()
            recommend_count += user_reviews['recommend'].sum()
            total_reviews += len(user_reviews)
            item_ids.update(user_reviews['item_id'].unique())

        if total_reviews > 0:
            porcentaje = (recommend_count/total_reviews) * 100
        else:
            porcentaje = 0

        items_count = len(item_ids)

        user_data = {
            'Cantidad de dinero gastado': Cantidad,
            'Recomendado Porcentaje': porcentaje,
            'Cantidad de items': items_count
        }

        return user_data
    
    except Exception as e:
        return {'message': f'Error: {str(e)}'}

    
df_steam2 = pd.read_csv('./data/steam_games.csv')

@app.get("/recomendacion_juego/{product_id}")
async def recomendacion_juego(product_id: int):
    try:
        # Obtener el ID del juego
        target_game = df_steam2[df_steam2['id'] == product_id]

        if target_game.empty:
            return {"message": "No se encontró el juego de referencia."}

        # Combina las etiquetas (tags) y géneros en una sola cadena de texto
        target_game_tags_and_genres = ' '.join(target_game['tags'].fillna('').astype(str) + ' ' + target_game['genres'].fillna('').astype(str))

        # Crea un vectorizador TF-IDF
        tfidf_vectorizer = TfidfVectorizer()

        # Configura el tamaño del lote para la lectura de juegos
        chunk_size = 100  # Tamaño del lote (puedes ajustarlo según tus necesidades)
        similarity_scores = None

        # Procesa los juegos por lotes utilizando chunks
        for chunk in pd.read_csv('./Data/steam_games.csv', chunksize=chunk_size):
            # Combina las etiquetas (tags) y géneros de los juegos en una sola cadena de texto
            chunk_tags_and_genres = ' '.join(chunk['tags'].fillna('').astype(str) + ' ' + chunk['genres'].fillna('').astype(str))

            # Aplica el vectorizador TF-IDF al lote actual de juegos y al juego de referencia
            tfidf_matrix = tfidf_vectorizer.fit_transform([target_game_tags_and_genres, chunk_tags_and_genres])

            # Calcula la similitud entre el juego de referencia y los juegos del lote actual
            if similarity_scores is None:
                similarity_matrix = cosine_similarity(tfidf_matrix)
                similarity_scores = cosine_similarity(similarity_matrix, similarity_scores)
            else:
                similarity_matrix = cosine_similarity(tfidf_matrix)
                similarity_scores = cosine_similarity(similarity_matrix, similarity_scores)

        if similarity_scores is not None:
            # Obtiene los índices de los juegos más similares
            similar_games_indices = similarity_scores[0].argsort()[::-1]

            # Recomienda los juegos más similares (puedes ajustar el número de recomendaciones)
            num_recommendations = 5
            recommended_games = df_steam2.loc[similar_games_indices[1:num_recommendations + 1]]

            # Devuelve la lista de juegos recomendados
            return recommended_games[['app_name','id']].to_dict(orient='records')

        return {"message": "No se encontraron juegos similares"}

    except Exception as e:
        return {"message": f"Error: {str(e)}"}