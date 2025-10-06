<script>
  import { onMount } from "svelte";
  import { resolveRoute } from "$app/paths";
  import Spinner from "$components/utils/Spinner.svelte";
  import { UserClass } from "$lib/store.svelte.js";
  import ClickToCopy from "$components/utils/ClickToCopy.svelte";
  import { toast } from "svoast"; // https://svoast.vercel.app/
  import { customErrorTypes } from "$lib/customErrors";

  let spinner;
  let user = new UserClass();

  let makeToast = {
    success: (msg) => {
      toast.success(msg);
    },
    error: (error) => {
      toast.error(
        `<h1>Error</h1>
        <p style="color: lightyellow">${error}</p>`,
        {
          infinite: true,
          closable: true,
          rich: true,
        }
      );
    },
    attention: (msg) => {
      toast.attention(msg);
    },
  };

  onMount(async () => {
    try {
      spinner.start();
      await user.pull(); // The `await` is critical for both data and error handling
    } catch (error) {
      console.log(error);
      if (
        [
          customErrorTypes.ForbiddenError,
          customErrorTypes.UnauthorizedError,
        ].includes(error.name)
      ) {
        window.location.href = "/";
      }
      makeToast.error(error.stack);
    } finally {
      spinner.stop();
    }
  });

  let onThrowError = () => {
    makeToast.error("Why did you click on me?");
  };

  let onNewUsername = () => {
    try {
      user.data.username = new Date();
      makeToast.attention(`New username: ${user.data.username}`);
      console.log("Updated User: ", $state.snapshot(user.data));
    } catch (error) {
      makeToast.error(error.stack);
    }
  };

  let onLatest = async () => {
    spinner.start();
    try {
      const results = await user.pull();
      makeToast.success(`Latest user data successfully pulled: ${results}`);
    } catch (error) {
      makeToast.error(error.stack);
    } finally {
      spinner.stop();
    }
  };

  let onSave = async () => {
    spinner.start();
    try {
      await user.push();
      makeToast.success("Latest user data successfully pushed");
    } catch (error) {
      console.error(error);
      makeToast.error(error.stack);
    } finally {
      spinner.stop();
    }
  };
</script>

<Spinner bind:this={spinner} />

<h1>Example Page</h1>

<div>
  <span id="usernameId">
    {(user.data && user.data.username) || "no username given"}
  </span>
  <ClickToCopy target="#usernameId" />
</div>

<button onclick={onNewUsername}>New Username</button>
<button onclick={onLatest}>Get Latest</button>
<button onclick={onSave}>Save</button>
<button onclick={onThrowError}>Do Not Click Me</button>
