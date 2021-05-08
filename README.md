# Projeto: Sistema Anotação de Vídeo com dados fisiológicos para análise de emoções

## Processo responsável pela obtenção da informação da câmara *intel realsense* e codificar a informação obtida para ser enviada para o servidor e para a aplicação

### `camera.py`:
* Thread que acede à câmara e regista em memória as frames;
* Esta thread bloqueia o acesso à memória enquanto insere uma frame nesta.

### `connector.py`:
* Thread que retira as frames da memória da thread acima e limpa a memória.




### Páginas 

page -> página de visualização do vídeo "em tempo real"

after_recording -> página de visualização do vídeo e anotações

myvideos -> página com os vídeos associados a uma conta

base -> navbar

annotations -> aside elements

login, signup & update profile


**TODO**:
- timeline do vídeo (para rever anotações)
