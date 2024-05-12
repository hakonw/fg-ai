<script lang="ts">
  import Slider from "@smui/slider";

  export let sensitivity;

  const minValue = 20;
  const maxValue = 50;
  const stepValue = 0.1;

  const normalizedValue = (v: number) =>
    Math.round(((v - minValue) * 254) / (maxValue - minValue));
  const toHex = (n: number) => n.toString(16).padStart(2, "0");
</script>

{#if sensitivity > 40}
<small>Høy sensitivitet kan mange bilder!. Pass på at du er på wifi!</small>
{/if}

<div class="slider">
  <Slider
    style="--mdc-theme-primary: #{toHex(normalizedValue(sensitivity)) +
      '00' +
      toHex(255 - normalizedValue(sensitivity))};"
    bind:value={sensitivity}
    min={minValue}
    max={maxValue}
    step={stepValue}
    input$aria-label="Gjenkjennings sensitivitet verdi"
  />
</div>
<p>Sensitivitet: {sensitivity}</p>
{#if sensitivity === minValue}
  <p>Får du noe her da? Prøv litt høyere</p>
{/if}
{#if sensitivity === maxValue}
  <p>Du vet du kan få 2000+ bilder? Right?</p>
{/if}

<style>
  .slider {
    width: 50vw;
  }
</style>
