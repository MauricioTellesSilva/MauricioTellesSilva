a

O core da aplicação é uma pipeline de CI/CD que consome dados brutos da API do GitHub, processa métricas atômicas do profile e injeta o payload processado diretamente no `README.md` através de um split posicional estrito.

A stack roda com Python nativo (`requests`, `re`, `time`) encapsulado em um runner Ubuntu do GitHub Actions.

---

### 1. Provisionamento de Credenciais (Auth & Escopo)

A `GITHUB_TOKEN` padrão do workflow não possui privilégios para varrer dados históricos globais (especialmente repositórios privados e organizações). É mandatório o uso de um PAT.

1. **Geração do PAT:** Criar um *Personal Access Token (Classic)*.
* **Escopos obrigatórios:** `repo` (full control), `read:user` e `user:email`.


2. **Injeção de Secret:** No repositório do seu perfil, expor o token em `Settings > Secrets and variables > Actions`.
* **Key:** `METRICS_TOKEN`
* **Value:** [Token gerado]



---

### 2. Configuração do Target (`README.md`)

O script realiza um parse bruto baseado em delimitadores fixos. Insira as tags de marcação HTML exatamente onde as métricas devem ser renderizadas no seu documento:

```markdown

```

* **Regra de Mutabilidade:** O buffer contido entre essas duas tags é considerado volátil. Qualquer caractere ali dentro será limpo e sobrescrito a cada runtime da pipeline. O conteúdo fora das tags (acima ou abaixo) permanece imutável e protegido contra corrupção.

---

### 3. Diretrizes do CI/CD Runner (`text_stats.yml`)

O arquivo de workflow deve ser mapeado em `.github/workflows/text_stats.yml` seguindo as seguintes especificações de infraestrutura:

* **Triggers:** Agendamento via Cron Job (sugerido: `0 */12 * * *` para rodar a cada 12h), gatilho manual (`workflow_dispatch`) e hooks de `push` nas branches principais (`main`/`master`).
* **Permissions:** Configurar explicitamente `contents: write`, permitindo que o `github-actions[bot]` tenha permissão de escrita para commitar o diff de volta no repositório upstream.
* **Environment Variables:** Mapear o contexto do runtime injetando a secret `GH_TOKEN: ${{ secrets.METRICS_TOKEN }}` e o identificador do owner `GH_USERNAME: ${{ github.repository_owner }}`.

---

### 4. Lógica de Execução da Engine (Script Python Interno)

O script automatizado executa um pipeline sequencial dividido em 7 etapas:

1. **Discovery:** Realiza um scan no diretório raiz do runner para capturar o arquivo `README.md` (validação com tratamento *case-insensitive*).
2. **Global Aggregation:** Consome os endpoints da Search API (`/search/commits` e `/search/issues?q=author:{user}+type:pr`). Essa abordagem contorna o throttling e os limites severos de paginação da API de eventos padrão do GitHub, garantindo o histórico real acumulado.
3. **Repo Mapping:** Realiza o crawler em `/user/repos` paginando de 100 em 100 itens. Filtra apenas objetos onde a propriedade `fork == false`.
4. **Metrics Parsing (O ponto crítico):** Itera sobre cada repositório mapeado batendo no endpoint `/stats/contributors`. O script faz o parse do array de objetos das semanas (`weeks`), acumulando as propriedades `a` (linhas adicionadas) e `d` (linhas deletadas) **exclusivamente** quando o nó `contributor.author.login` der match exato com o seu username. Isso garante que linhas de terceiros em projetos colaborativos não poluam o seu report.
5. **Language Byte Analytics:** Consome `/languages` em cada repo, consolida o volume bruto de bytes e extrai o Top 4 proporcional das tecnologias dominantes.
6. **LaTeX Styling:** Trata os inteiros finais com formatação de milhar (`{:,}`) e encapsula os outputs em blocos matemáticos do LaTeX (`$\color{#HEX}{\mathbf{+value}}$`). Isso força a injeção cromática direto no Markdown, garantindo legibilidade tanto em Dark Mode quanto em Light Mode na UI do GitHub.
7. **Safe Positional Split:** O script lê o README, executa um `.split('')`, isola o Header, pega a segunda metade e quebra no `` para isolar o Footer. Ele reconstrói a string concatenando `[Header, Tag_Abertura, Novo_Payload, Tag_Fechamento, Footer]` e commita via Git.

---

### 5. Troubleshooting & Status Codes (Fail-Safe)

* **Exit Code 1 (Tag Error):** Se os delimitadores não forem validados na string do README, o script aborta a execução imediatamente com erro de barreira, impedindo que um payload vazio ou malformado zere o seu arquivo original.
* **HTTP Status 202 (Accepted):** O GitHub gera cache sob demanda para estatísticas de contribuidores. Se o endpoint retornar `202`, significa que os dados estão sendo processados no upstream. O script intercepta esse status, joga o repositório em uma fila de espera, executa um `time.sleep(25)` no runtime e faz o re-fetch para não perder o report daquela pipeline.
* **HTTP Status 401 (Unauthorized):** Indica falha no handshake com a API. Validar escopos e expiração do `METRICS_TOKEN` cadastrado nas secrets.