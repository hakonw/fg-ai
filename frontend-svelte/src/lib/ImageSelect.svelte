<script lang="ts">
  export let image: string;
  let fileinput: HTMLInputElement;

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
</script>

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

<style>
  .avatar {
    cursor: pointer;
    display: flex;
    max-width: 200px;
  }

  .upload {
    display: flex;
    height: 50px;
    width: 50px;
    cursor: pointer;
  }
</style>
