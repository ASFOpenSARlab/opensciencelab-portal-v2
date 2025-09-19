class Common {
  constructor(id, getApiUri, postApiUri) {
    this.id = id;
    this.getApiUri = getApiUri;
    this.postApiUri = postApiUri;
    this.store = $state({});
  }

  pull = async () => {
    const response = await fetch(this.getApiUri, {
      method: "GET",
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    console.log("Success:", data);

    this.data = data;

    return data;
  };

  push = async () => {
    const response = await fetch(this.postApiUri, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(this.data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const result = await response.json();
    return result;
  };

  get data() {
    console.log(
      "get data",
      $state.snapshot(this.store),
      $state.snapshot(this.store[this.id])
    );
    return this.store[this.id];
  }

  set data(newData) {
    this.store[this.id] = newData;
    console.log(
      "set data",
      $state.snapshot(this.store),
      $state.snapshot(this.store[this.id])
    );
  }
}

export class UserClass extends Common {
  constructor() {
    super(Symbol("UserClass"), "/portal/users/whoami", "/portal/users/whoami");
  }
}
