<script lang="ts">
  import type { ImageData } from "src/App.svelte";

  export let imageDatas: ImageData[];

  export let openInTab: boolean;
</script>

<p>Fant {imageDatas.length} bilder.</p>
<p>
  VIKTIG: Klikk på bildet for å få fg sin side der du kan laste ned
  full-versjonen!
</p>
{#each imageDatas as imageData}
  {#if imageData !== undefined}
    {#if openInTab === true}
      {window
        .open("https://fg.samfundet.no" + imageData.arkiv, "_blank")
        .focus()}
    {/if}
    <div id="card">
      <p>{imageData.motive} - {imageData.date}</p>
      <a href="https://fg.samfundet.no{imageData.arkiv}" target="_blank">
        <img
          style="max-width:90%;"
          src="https://fg.samfundet.no{imageData.thumb}"
          alt={imageData.motive}
        />
      </a>
    </div>
  {/if}
{/each}

<style>
  #card {
    border-top: 1px;
    border-left: 0;
    border-right: 0;
    border-bottom: 0;
    border-style: solid;
    border-color: gainsboro;
  }
</style>
