# Relatório de acessibilidade

Validação do dashboard do Projeto Impressoras segundo a **WCAG 2.1, nível AA**.

| | |
|---|---|
| **Ferramenta** | Google Lighthouse 12.8.2 (Chrome em modo headless) |
| **Página avaliada** | `http://127.0.0.1:5000/` (aba Monitoramento, 48 impressoras) |
| **Data da última execução** | 27/10/2026 |
| **Nota final** | **100 / 100** |
| **Auditorias automáticas** | 23 aprovadas, 0 reprovadas |

Os arquivos `lighthouse.report.html` (relatório completo, abra no navegador) e `lighthouse.report.json` (dados brutos) estão nesta pasta.

---

## Como reproduzir

Com o servidor rodando (`venv\Scripts\python app.py`), em outro terminal:

```powershell
npx lighthouse http://127.0.0.1:5000/ --only-categories=accessibility --chrome-flags="--headless=new" --output=html --output=json --output-path=docs/acessibilidade/lighthouse
```

Pelo navegador, sem instalar nada: abra a página, pressione `F12`, vá na aba **Lighthouse**, marque apenas **Accessibility** e clique em *Analyze page load*.

---

## Problemas encontrados e corrigidos

A primeira execução resultou em **96/100**, com dois problemas. As correções levaram o resultado a 100.

### 1. Contraste insuficiente no nome do modelo (peso 7)

O texto do modelo dentro dos cards usava `opacity: 0.75`. A transparência mistura a cor do texto com o fundo e derrubava o contraste real:

| Card | Com 0,75 | Com 0,85 | Mínimo |
|---|---|---|---|
| Normal | 3,84:1 | **4,79:1** | 4,5:1 |
| Atenção | 3,94:1 | **4,93:1** | 4,5:1 |
| Crítico | 4,58:1 | **5,72:1** | 4,5:1 |
| Offline | 3,78:1 | **4,76:1** | 4,5:1 |

**Correção:** transparência ajustada para `0.85`, mantendo a hierarquia visual.

Esse problema não havia sido detectado na conferência manual de cores, porque a transparência não aparece no valor declarado no CSS. Foi o principal ganho de rodar a ferramenta.

### 2. Nome acessível diferente do texto visível (critério 2.5.3)

Os contadores e os cards tinham `aria-label` que **substituía** o texto visível:

```html
<!-- antes -->
<div class="contador contador-online" aria-label="Mostrar apenas as impressoras online">
    <div class="contador-titulo">ONLINE</div>
    <div class="contador-numero">45</div>
</div>
```

Quem usa comando de voz diz "clicar em ONLINE", mas o sistema registrava o elemento como "Mostrar apenas as impressoras online" — e o comando falhava.

**Correção:** o `aria-label` foi removido e o complemento passou a ser um texto oculto dentro do elemento, somando-se ao texto visível em vez de substituí-lo:

```html
<!-- depois -->
<div class="contador contador-online" role="button" tabindex="0" aria-pressed="false">
    <div class="contador-titulo">ONLINE</div>
    <div class="contador-numero">45</div>
    <span class="apenas-leitor">Mostrar apenas as impressoras online</span>
</div>
```

O nome lido passa a ser "ONLINE 45 Mostrar apenas as impressoras online": contém o texto visível e mantém a explicação.

### 3. Contraste do rodapé

Detectado na segunda execução: `#6b7280` sobre o fundo cinza da página dava 4,46:1, pouco abaixo do mínimo de 4,5:1.

**Correção:** cor alterada para `#4b5563`.

---

## O que foi implementado

| Recurso | Onde |
|---|---|
| Rótulos e papéis (`role`, `aria-*`) | Cards, contadores, abas, janela de detalhes |
| Avisos de mudança (`aria-live`) | Status do sistema, contador de atualização, total filtrado |
| Navegação por teclado | `Tab` alcança cards e filtros; `Enter` e `Espaço` acionam |
| Foco visível | Contorno azul de 3px (6,70:1 de contraste) |
| Gerenciamento de foco | Ao abrir a janela o foco entra nela; ao fechar volta ao card de origem |
| Foco preso na janela | `Tab` circula apenas entre os elementos da janela aberta |
| Situação sem depender de cor | Ícone e texto em cada card: ✓ Normal, ⚠ Atenção, ✕ Crítico, ⊘ Offline |
| Contraste | 28 combinações verificadas, todas acima do mínimo |
| Emojis ocultos de leitores | `aria-hidden` nos ícones decorativos |
| Tabela com cabeçalhos ligados | `scope="col"` na tabela do top 10 |

A verificação de contraste virou teste automatizado em `tests/test_contraste.py`, com 30 testes. Se alguém trocar uma cor por uma mais clara, os testes falham.

---

## Verificações manuais

O Lighthouse lista 10 itens que nenhuma ferramenta consegue avaliar sozinha. Foram conferidos à mão:

| Verificação | Situação |
|---|---|
| Controles alcançáveis pelo teclado | OK — abas, contadores e os 48 cards |
| Elementos indicam propósito e estado | OK — `aria-pressed` nos filtros, `aria-selected` nas abas |
| Ordem do `Tab` é lógica | OK — cabeçalho, abas, contadores, cards |
| Ordem visual acompanha a ordem do HTML | OK |
| Foco não fica preso por engano | OK — a janela prende o foco de propósito e o `Esc` libera |
| Foco vai para o conteúdo novo | OK — ao abrir a janela o foco entra nela |
| Uso de elementos de marcação do HTML5 | OK — `header`, `main`, `section` |
| Conteúdo fora da tela escondido de leitores | OK — abas inativas usam `display: none` |
| Controles personalizados têm rótulo | OK — corrigido no item 2 acima |
| Controles personalizados têm papel ARIA | OK — `role="button"` nos cards e contadores |

---

## Limitações

- A validação cobriu a **aba Monitoramento**. A aba Análise é carregada na mesma página, mas o Lighthouse avalia apenas o que está visível na carga inicial.
- A janela de detalhes abre por interação, então não entra na análise automática. Foi verificada à mão e por testes automatizados (foco ao abrir e fechar).
- Nenhum teste foi feito com leitores de tela reais (NVDA, JAWS ou VoiceOver). É a evolução natural desta etapa.
