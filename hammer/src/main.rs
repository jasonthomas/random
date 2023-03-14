use std::env;
use tokio;
use reqwest::Client;
use futures::{stream, StreamExt};

#[tokio::main(flavor = "multi_thread", worker_threads = 10)]
async fn main() {
    let args: Vec<String> = env::args().collect();
    let client = Client::new();

    let CONCURRENT_REQUESTS:usize = args[2].parse::<usize>().unwrap();
    let total_requests:usize = args[3].parse::<usize>().unwrap();
    let urls = vec![&args[1]; total_requests];

    let bodies = stream::iter(urls)
        .map(|url| {
            let client = &client;
            async move {
                let resp = client.get(url).send().await?;
                resp.bytes().await
            }
        })
        .buffer_unordered(CONCURRENT_REQUESTS);

    bodies
        .for_each(|b| async {
            match b {
                Ok(b) => println!("Got {} bytes", b.len()),
                Err(e) => eprintln!("Got an error: {}", e),
            }
        })
        .await;
}
