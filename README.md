# Projeto - Adapter

## Processo responsável pela obtenção da informação da câmara *intel realsense* e codificar a informação obtida para ser enviada para o servidor e para a aplicação

### `camera_2.py`:
* Thread que acede à câmara e regista em memória as frames;
* Esta thread bloqueia o acesso à memória quando está a mexer nela.

### `connector.py`:
* Thread que retira as frames da memória da thread acima e limpa a memória.
