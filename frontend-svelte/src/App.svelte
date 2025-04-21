<script context="module" lang="ts">
  export type ImageData = {
    arkiv: string;
    date: string;
    download_link: string;
    motive: string;
    place: string;
    thumb: string;
    distance: number;
  };
</script>

<script lang="ts">
  import type { SnackbarComponentDev } from "@smui/snackbar";
  import Snackbar, { Label } from "@smui/snackbar";
  import CircularProgress from "@smui/circular-progress";
  import Sensitivity from "./lib/Sensitivity.svelte";
  import Result from "./lib/Result.svelte";
  import ImageSelect from "./lib/ImageSelect.svelte";
  import Selector from "./lib/Selector.svelte";
  import {Choice, type ChoiceT} from "./lib/SelectorChoice";

  let image: string; // data:image/jpeg;base64
  let snackMsg: string;
  let snackbarError: SnackbarComponentDev;
  let imageDatas: ImageData[] | undefined;
  let loading = false;

  export let server: string;
  let defaultSensitivity: number = 3;
  let sensitivity: number = defaultSensitivity;
  let openAllInNewTab: false;
  let mode: ChoiceT = Choice.bestMatch;
  
  const send = () => {
    if (image === undefined || image === "") {
      snackMsg = "Du må velge et bilde..";
      snackbarError.open();
      return;
    }

    const body = {
      sensitivity: sensitivity,
      image: image,
      mode: mode.value
    };
    loading = true;

    const sendResponse = fetch(server, {
      method: "post",
      body: JSON.stringify(body),
      headers: {
        "Content-Type": "application/json",
      },
    });
    
    sendResponse
      .then((res) => {
        if (!res.ok) {
          return res.text().then(text => { throw new Error(text) })
        }
        return res.json();
      })
      .then(d => {console.log(d); return d})
      .then((data: ImageData[]) => (imageDatas = data))
      .catch((e) => {
        console.error(e);
        snackMsg = e.toString();
        snackbarError.open();
        imageDatas = undefined;
      })
      .finally(() => (loading = false));
  };
</script>

<main>
  <h1>Ai av Fotogjengens arkiv 📷</h1>
  <div id="info">
    <p>Laget av Wardeberg.</p>
    <p>
      Denne tjenesten lagrer <strong>ikke</strong> bildene du laster opp! Men bruker cookies for google analytics.
    </p>
    <small>
      Og ja, den finner for mange feil bilder, men heller det enn motsatt.¨
    </small>
        <p><small>Tjenesten inneholder ikke alle bilder. Både nye og veldig gamle bilder kan være uprosessert</small></p>
  </div>

  <div id="bilde" class="flexed">
    <h2>Velg bilde</h2>
    <p>Step 1: Velg et bilde med bare et ansikt. Et bra bilde er viktig her!</p>
    <small>
      Du MÅ ha tillatelse av personen du laster opp! Missbruk er ikke tillatt.
    </small>
    <ImageSelect bind:image />
  </div>
  
  <div id="modus" class="flexed">
    <h2> Modus</h2>
    <Selector bind:selected={mode}></Selector>
<!--    <p>{Choice.bestMatch.name} vil gi de 100 bildene som ligner mest</p>-->
<!--    <p>{Choice.sensitivity.name} bruker en grense og gir kronologiske bilder</p>-->
  </div>

  {#if mode?.value === "sensitivity"}
    <div id="sensitivitet" class="flexed">
      <h2>Gjenkjenningssensitivitet</h2>
      <p>
        Step 2: Velg en sensitivitet. Prøv litt rundt {defaultSensitivity}. Om du får ingen
        eller bare feil matches, prøv et annet bilde!
      </p>
      <p>Høyere verdi betyr flere mulige bilder (da også flere feil bilder).</p>
      <Sensitivity bind:sensitivity />
    </div>
  {/if}

  <div id="send" class="flexed">
    <h2>Finn bilder</h2>
    <p>
      Noen bilder vil ikke laste inn fordi de er internbilder og man må da være
      logget inn.
    </p>
    <label>
      <input type="checkbox" bind:checked={openAllInNewTab} /> Åpne i egen fane?
    </label>
    <small>(Dette tillater deg å kunne se internbildene)</small>
    {#if openAllInNewTab}
      <p>
        1. Pass på at du er logget inn på <a
          href="https://foto.samfundet.no/arkiv/DIGGC/18/19/">fg.samfundet.no</a
        >
      </p>
      <p>
        2. At du tillater at denne siden åpner flere faner. (Nettleseren vil
        spørre deg etter du trykker kjør)
      </p>
    {/if}

    <button on:click={() => send()}> Kjør </button>

    {#if loading === true}
      <CircularProgress style="height: 32px; width: 32px; margin-top: 16px" indeterminate />
      <p>
        VIKTIG: Klikk på bildet for å få fg sin side der du kan laste ned
        full-versjonen!
      </p>
    {/if}

    <Snackbar bind:this={snackbarError}>
      <Label>{snackMsg}</Label>
    </Snackbar>
  </div>

  <div id="result" class="flexed">
    {#if imageDatas !== undefined}
      <Result {imageDatas} openInTab={openAllInNewTab} />
    {/if}
  </div>

  <p><a href="https://github.com/hakonw/fg-ai">Kildekode på github</a></p>
</main>

<style>
  main {
    text-align: center;
    padding: 1em;
    max-width: 90%;
    margin: 0 auto;
  }

  h1 {
    color: #ff3e00;
    font-size: 4em;
    font-weight: 100;
  }

  h2 {
    color: #ff4000;
    font-size: 3em;
    font-weight: 100;
  }

  button {
    border-color: #ff3e00;
  }

  .flexed {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-flow: column;
  }
</style>
