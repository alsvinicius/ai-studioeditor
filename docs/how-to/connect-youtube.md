# Como conectar o YouTube

Use **Configurações → YouTube**, em <http://localhost:8000/settings>, para conectar uma conta a todos os projetos do estúdio. A página funciona mesmo sem uma gravação aberta.

## Preparar e importar a credencial

1. Crie ou selecione um projeto no Google Cloud e habilite a YouTube Data API v3.
2. Configure a tela de consentimento OAuth e adicione sua conta como usuária de teste, se o projeto estiver em modo de teste.
3. Em **Configurações**, copie o **URI de redirecionamento** mostrado pelo estúdio.
4. No Google Cloud, crie uma credencial OAuth do tipo **Aplicativo Web**, adicione o URI copiado e baixe o JSON.
5. Na página de configurações do estúdio, selecione **Importar JSON OAuth** e escolha o arquivo. Após a validação, o estado passa a **Credencial OAuth configurada neste estúdio**.
6. Selecione **Conectar YouTube**. Autorize a conta na nova aba e volte às configurações para conferir **Conectado**.

O JSON é salvo localmente em `data/youtube-client-secret.json` com permissão 0600; seu conteúdo não é devolvido pela API. A credencial enviada pela interface prevalece sobre `YOUTUBE_CLIENT_SECRETS`. A configuração por ambiente e o arquivo `secrets/client_secret.json` continuam disponíveis como alternativa. Nunca adicione credenciais ao Git.

## Enviar um projeto revisado

1. Exporte a edição aprovada e abra a aba **Publicação** do projeto.
2. Selecione os vídeos e revise título, descrição, capítulos e tags.
3. Se a conta ainda não estiver conectada, use o link **Configurações**. A conexão vale para os demais projetos.
4. Escolha **Aprovar e enviar como privado** e confirme a revisão para iniciar o envio.
5. Confira os links retornados no YouTube Studio. Para publicar ao público, altere a visibilidade manualmente no Studio.

A aplicação solicita `youtube.upload` para vídeos e `youtube.force-ssl` para anexar faixas de legenda. Vídeos selecionados recebem faixas SRT no idioma de origem e para cada idioma traduzido e selecionado; VTT continua disponível para download. O token local é salvo em `data/youtube-token.json`, fora do Git.

## Trocar a credencial ou desconectar

Use **Desconectar** na página global para remover a autorização local de todos os projetos. Os arquivos exportados continuam disponíveis. Para trocar a credencial, importe outro JSON; a conexão anterior é removida e deve ser autorizada novamente. Enquanto um upload estiver em andamento, o aplicativo bloqueia essas mudanças.

## Se a conexão falhar

- Confirme que a YouTube Data API v3 está habilitada e o cliente é do tipo Web.
- Confira se o URI de redirecionamento é idêntico ao mostrado nas configurações. O endereço padrão é `http://localhost:8000/api/youtube/callback`.
- Permita a nova aba de autorização se o navegador bloquear pop-ups.
- Se a autorização for negada ou expirar, use **Reconectar conta** nas configurações.
- Se um upload perder a conexão antes de retornar um ID, confira o YouTube Studio antes de repetir. O app bloqueia repetições com resultado desconhecido.

Consulte a documentação oficial de [upload de vídeo](https://developers.google.com/youtube/v3/guides/uploading_a_video), [inserção de legendas](https://developers.google.com/youtube/v3/docs/captions/insert) e [OAuth para aplicações Web](https://developers.google.com/identity/protocols/oauth2/web-server) para preparar o projeto no Google Cloud.
