<script lang="ts">
  import Slider from "@smui/slider";
  import type { SnackbarComponentDev } from "@smui/snackbar";
  import Snackbar, { Label } from "@smui/snackbar";
  import CircularProgress from "@smui/circular-progress";

  let image: string; // data:image/jpeg;base64
  let fileinput: HTMLInputElement;
  let snackbarError: SnackbarComponentDev;
  let imageDatas: ImageData[];
  let loading = false;

  type ImageData = {
    arkiv: string;
    date: string;
    download_link: string;
    motive: string;
    place: string;
    thumb: string;
  };

  export let server: string;

  const onFileSelected = (e) => {
    if (e.target.files.length === 0) {
      return;
    }
    let selectedImage = e.target.files[0];
    let reader = new FileReader();
    reader.readAsDataURL(selectedImage);
    reader.onload = (e) => {
      image = e.target.result.toString();
    };
  };

  let value = 45; // Note: is 10x regular sensitivity, sadly a bad name too

  const send = () => {
    if (image === undefined || image === "") {
      // TODO warning, needs image
      snackbarError.open();
      return;
    }

    const body = {
      sensitivity: value,
      image: image,
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
      .then((res) => res.json())
      .then((data: ImageData[]) => (imageDatas = data))
      .catch((e) => {
        console.error(e);
        snackbarError.open();
      })
      .finally(() => (loading = false));
  };
</script>

<main>
  <h1>Ai av Fotogjengens arkiv 📷</h1>
  <div id="info">
    <p>Laget av Wardeberg. Ser du meg, kjøp meg gjerne en øl 👉👈</p>
    <p>
      Denne tjenesten lagrer <strong>ikke</strong> bilder eller noe informasjon om
      deg ❤️
    </p>
    <small>
      Og ja, den finner for mange feil bilder, men heller det enn motsatt.¨
    </small>
  </div>

  <div id="bilde">
    <h2>Velg bilde</h2>
    {#if image}
      <img
        class="avatar"
        src={image}
        alt="you"
        on:click={() => {
          fileinput.click();
        }}
      />
    {:else}
      <img
        class="avatar"
        src="https://cdn4.iconfinder.com/data/icons/small-n-flat/24/user-alt-512.png"
        alt=""
        on:click={() => {
          fileinput.click();
        }}
      />
    {/if}
    <img
      class="upload"
      src="https://static.thenounproject.com/png/625182-200.png"
      alt=""
      on:click={() => {
        fileinput.click();
      }}
    />
    <div
      class="chan"
      on:click={() => {
        fileinput.click();
      }}
    >
      Choose Image
    </div>
    <input
      style="display:none"
      type="file"
      accept=".jpg, .jpeg, .png"
      on:change={(e) => onFileSelected(e)}
      bind:this={fileinput}
    />
  </div>

  <div id="sensitivitet">
    <h2>Gjenkjennings sensitivitet</h2>
    <p>Høyere verdi betyr flere mulige bilder (da også flere feil bilder).</p>
    <div class="slider">
      <Slider
        style="--mdc-theme-primary: #{Math.round(value * 3)
          .toString(16)
          .padStart(2, '0') +
          '00' +
          (255 - Math.round(value * 3)).toString(16).padStart(2, '0')};"
        bind:value
        min={20}
        max={65}
        step={0.1}
        input$aria-label="Gjenkjennings sensitivitet verdi"
      />
    </div>
    <p>Sensitivitet: {value}</p>
    {#if value === 0.05 || value === 0.8}
      <p>Kan du ikke?</p>
    {/if}
  </div>
  <div id="send">
    <h2>Sending</h2>
    <p>
      TODO åpne i new tab (Tillater internbilder) eller åpne alle offentlige
      bilder her
    </p>
    <button on:click={() => send()}> Kjør </button>

    {#if loading === true}
      <CircularProgress style="height: 32px; width: 32px;" indeterminate />
      <p>
        VIKTIG: Klikk på bildet for å få fg sin side der du kan laste ned
        full-versjonen!
      </p>{/if}

    <Snackbar bind:this={snackbarError}>
      <Label>Noe ble feil.</Label>
    </Snackbar>
  </div>
  <div id="result">
    {#if imageDatas !== undefined}
      <p>Funnet {imageDatas.length} bilder.</p>
      <p>
        VIKTIG: Klikk på bildet for å få fg sin side der du kan laste ned
        full-versjonen!
        {#each imageDatas as imageData}
          <!-- {window.open("https://fg.samfundet.no" + imageData.arkiv, '_blank').focus()} -->
          <pre> {imageData.thumb} </pre>
          <img
            style="max-width:90%;"
            src="https://fg.samfundet.no{imageData.thumb}"
            alt={imageData.motive}
          />
        {/each}
      </p>{/if}
  </div>
  <p><a href="todo">Kildekode på github</a></p>
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

  .slider {
    width: 50%;
  }

  #sensitivitet {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-flow: column;
  }

  #send {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-flow: column;
  }

  #bilde {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-flow: column;
  }

  .upload {
    display: flex;
    height: 50px;
    width: 50px;
    cursor: pointer;
  }
  .avatar {
    cursor: pointer;
    display: flex;
    max-width: 200px;
  }
</style>
