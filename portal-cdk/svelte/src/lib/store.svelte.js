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
    return this.store[this.id];
  }

  set data(newData) {
    this.store[this.id] = newData;
  }
}

export class UserClass extends Common {
  constructor() {
    super(
      Symbol("UserClass"),
      "https://dq3yyi71b8t6w.cloudfront.net/portal/users/whoami",
      "https://dq3yyi71b8t6w.cloudfront.net/portal/users/whoami"
    );
  }
}
