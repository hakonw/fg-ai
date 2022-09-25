<script lang="ts">
  import type { ImageData } from "src/App.svelte";

  export let imageDatas: ImageData[];
</script>

<p>Fant {imageDatas.length} bilder.</p>
<p>
  VIKTIG: Klikk på bildet for å få fg sin side der du kan laste ned
  full-versjonen!
</p>
{#each imageDatas as imageData}
  <!-- {window.open("https://fg.samfundet.no" + imageData.arkiv, '_blank').focus()} -->
  <pre> {imageData.thumb} </pre>
  <img
    style="max-width:90%;"
    src="https://fg.samfundet.no{imageData.thumb}"
    alt={imageData.motive}
  />
{/each}

<style>
</style>
