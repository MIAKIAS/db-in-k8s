use actix_session::CookieSession;
use actix_web::{App, HttpServer};
use env_logger;
use log::info;
use o2versioner::scheduler::*;

fn init_logger() {
    let mut builder = env_logger::Builder::from_default_env();
    builder.target(env_logger::Target::Stdout);
    builder.filter_level(log::LevelFilter::Debug);
    builder.init();
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    init_logger();
    info!("Hello from scheduler exe");

    HttpServer::new(|| {
        App::new()
            .wrap(CookieSession::private(&[0; 32]).secure(false))
            .service(appserver_handler::greet)
            .service(appserver_handler::sql_handler)
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
