# Why Rust? The Smart Choice Behind Hugging Face’s Tokenizers

---

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 30.10.2025  
Modified: 30.10.2025  
Model: Qwen3-Max

---

> **Written for AI engineers who care not just about models but the robust, fast systems that power them.**

If you're working with Hugging Face Transformers, you've probably called `.encode()` or `.tokenize()` without thinking twice. But have you ever wondered what powers that lightning-fast tokenization under the hood?

Surprisingly, it’s not Python — and not even C or C++. It’s **Rust**.

In this article, we'll explore **why Hugging Face and other AI infrastructure teams chose Rust** to build high-performance tokenizers—and why this matters to you as an AI engineer.

## What Is a Tokenizer, Anyway?

Before diving into languages, let's recall the basics:

> A **tokenizer** converts raw text (like `"Hello, world!"`) into a list of **tokens** (e.g., `["Hello", ",", "world", "!"]`), which are then mapped to integers for model input.

This step is:

* **Required** for every NLP model.
* Often a **performance bottleneck** in data pipelines because it's I/O-intensive and involves frequent character, encoding, and hash-map lookups across billions of characters.
* Expected to be **fast, reliable, and safe**—even on messy real-world text.

The tokenizer must be **both efficient and robust**.

## Why Not Pure Python?

Python is great for prototyping, but it’s **too slow** for tokenization at scale. Looping character-by-character in Python can't compete with compiled code—especially when processing gigabytes of text.

Hence, serious tokenizers are written in **compiled systems languages**.

## Why Not C or C++?

C and C++ are classic choices for performance-critical code. And yes — **modern C++ (C++11 and beyond) is far safer than its reputation**. C++ offers several mechanisms that **eliminate or greatly reduce** the need for raw manual memory handling:

1. **RAII (Resource Acquisition Is Initialization)**  
   - The cornerstone of C++ resource management.
   - Resources (memory, file handles, etc.) are tied to object lifetimes.
   - Destructors automatically clean up when objects go out of scope.

2. **Smart pointers** (`std::unique_ptr`, `std::shared_ptr`, `std::weak_ptr`)  
   - Provide automatic, exception-safe memory management.
   - `unique_ptr` has **zero runtime overhead**—as efficient as raw pointers.
   - Prevent memory leaks and double-free bugs when used correctly.

3. **Standard containers** (`std::vector`, `std::string`, etc.)  
   - Manage their own memory safely and efficiently.
   - No need to call `new`/`delete` for most common use cases.

4. **Move semantics and copy control**  
   - Enable efficient, safe transfer of resources without deep copying.

So yes — **in well-written modern C++**, memory safety issues are *not inevitable*. Many large, safe, high-performance systems (e.g., game engines, browsers, databases) are built in C++ using these idioms.

Then why did Hugging Face choose Rust over C++? 

Even acknowledging C++'s capabilities, Rust offers **systematic guarantees** that C++ does not.

### The Key Difference: Safety by Default vs. Safety by Discipline

| Aspect | C++ (Modern) | Rust |
|-------|--------------|------|
| **Memory safety** | Achievable *if* you follow best practices and avoid unsafe patterns | **Enforced by the compiler**—you *cannot* compile code with use-after-free, data races, etc. (in safe code) |
| **Learning curve / team consistency** | Teams must be disciplined; it’s easy to accidentally use raw pointers or violate aliasing rules | Safety is **default and unavoidable**—even junior developers can’t introduce memory bugs (in safe code) |
| **Undefined behavior** | Still present (e.g., signed integer overflow, dangling references) | **No undefined behavior** in safe Rust |
| **Concurrency safety** | Possible with care, but data races are a runtime risk | Data races are **compile-time errors** |
| **Build & tooling** | Complex (CMake, headers, ABI stability, platform quirks) | Unified toolchain (`cargo`), reproducible builds, built-in testing/linting |

In C++, one accidental raw pointer, one missed move, one incorrect iterator—and you’ve opened the door to crashes or security flaws.

In Rust, the **borrow checker** stops these mistakes **before your code even runs**.

In other words:
> **C++ *can* be memory-safe, but Rust *must* be memory-safe (in safe code).**

> 💡 **Rust doesn’t trust you to be perfect. C++ does.**
> For foundational libraries used by millions, that trust is risky.

So, Hugging Face likely preferred **guaranteed safety by construction** over **safety by discipline**.

## Why Rust Shines for Tokenizers

Here’s how Rust specifically benefits tokenizer development:

### 1. Blazing Fast, Zero-Cost Abstractions

Rust compiles to optimized machine code (via LLVM), achieving **near-C++ speeds**. Operations like string slicing, UTF-8 handling, and hash lookups are extremely fast—but with compiler-enforced safety. The result? The `tokenizers` library is **10–100x faster** than pure Python alternatives.

### 2. Built-in UTF-8 Support

Text processing lives and dies by Unicode correctness. Rust’s `String` and `str` types are **UTF-8 by default**, preventing the notoriously painful encoding and slicing bugs common in other systems languages.

### 3. Fearless Concurrency

Tokenizers in production often run in multi-threaded servers. Rust ensures **no data races**—critical when sharing vocabularies or caches across threads—by enforcing its ownership rules at compile time.

### 4. Seamless Python Integration

Using **PyO3**, Rust code can be wrapped into Python packages with minimal overhead. That's how `tokenizers` delivers **native speed with a Pythonic API** that integrates easily into your ML ecosystem.

### 5. Reliable Builds & Distribution

With `cargo` (Rust’s build tool), compiling and packaging is consistent across platforms. Hugging Face ships pre-built wheels to PyPI—no user-side compilation needed—ensuring a smooth, reliable dependency for everyone.

## A Real-World Example: Hugging Face `tokenizers`

The [`tokenizers`](https://www.google.com/search?q=%5Bhttps://github.com/huggingface/tokenizers%5D\(https://github.com/huggingface/tokenizers\)) library:

* Is written **entirely in Rust**.
* Powers **all tokenization in Hugging Face Transformers**.
* Processes text **up to 10–100x faster** than pure Python alternatives.

And because it's in Rust, it's:

* **Secure** (no buffer overflows from malformed inputs).
* **Maintainable** (clear ownership model reduces bugs).
* **Scalable** (used in production by startups and Fortune 500s alike).

## Summary

Hugging Face chose **Rust** because it offers **C/C++-level performance with memory safety, modern tooling, and seamless Python integration**—making it ideal for building robust, high-performance NLP infrastructure.

This decision reflects a broader industry trend: **Rust is becoming the go-to language for safe, fast systems code**, especially in AI/ML infrastructure (e.g., also used in `llm.rs`, `candle`, `mlx-rs`, etc.).

## Takeaway for AI Engineers

You don't need to become a Rust expert tomorrow — but understanding **why Rust is used in AI infrastructure** helps you:

* Appreciate the tools you use (like `transformers`).
* Make better choices when building your own performance-critical pipelines.
* Recognize that **performance and safety aren't trade-offs**—they can and should coexist.

And who knows? You might even try writing your next preprocessing module in Rust! 🦀

## Further Reading

* [Hugging Face Tokenizers GitHub](https://github.com/huggingface/tokenizers)
* [The Rust Programming Language (Book)](https://doc.rust-lang.org/book/)
* [PyO3: Rust bindings for Python](https://pyo3.rs/)
