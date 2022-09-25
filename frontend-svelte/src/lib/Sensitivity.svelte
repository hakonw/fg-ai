<script lang="ts">
  import Slider from "@smui/slider";

  export let value = 45;
</script>

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

<style>
  .slider {
    width: 50vw;
  }
</style>
