import { onCall, HttpsError } from 'firebase-functions/v2/https';
import { onSchedule } from 'firebase-functions/v2/scheduler';
import { logger } from 'firebase-functions';
import axios from 'axios';
import * as cheerio from 'cheerio';
import { db } from './firebaseAdmin';

// Consultas por defecto que se refrescan automaticamente todos los dias.
// Un admin puede agregar mas categorias llamando a refreshStoreProducts desde un panel interno.
const DEFAULT_QUERIES = ['raqueta de tenis', 'pelotas de tenis', 'zapatillas de tenis', 'cuerdas de tenis'];

interface ScrapedProduct {
  mlId: string;
  title: string;
  price: number;
  imageUrl: string;
  mlUrl: string;
}

// Scraping directo del HTML de resultados de busqueda de Mercado Libre (mismo metodo
// usado anteriormente). Es fragil: Mercado Libre puede cambiar su markup o bloquear el
// scraping en cualquier momento, y sus Terminos de Servicio restringen el scraping
// automatizado. Si esto empieza a fallar seguido, la alternativa robusta es migrar a la
// API oficial (https://developers.mercadolibre.com.ar).
async function scrapeSearch(searchTerm: string): Promise<ScrapedProduct[]> {
  const url = `https://listado.mercadolibre.cl/${encodeURIComponent(searchTerm.replace(/\s+/g, '-'))}`;
  const { data: html } = await axios.get(url, {
    headers: {
      'User-Agent':
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36',
      'Accept-Language': 'es-CL,es;q=0.9',
    },
    timeout: 15000,
  });

  const $ = cheerio.load(html);
  const products: ScrapedProduct[] = [];

  $('li.ui-search-layout__item').each((_, el) => {
    const node = $(el);
    const link = node.find('a.ui-search-link, a.ui-search-item__group__element').first();
    const mlUrl = link.attr('href') || '';
    const title = node.find('h2.ui-search-item__title, .ui-search-item__title').first().text().trim();
    const fraction = node.find('.andes-money-amount__fraction').first().text().replace(/\./g, '');
    const price = parseInt(fraction, 10);
    const imageUrl =
      node.find('img.ui-search-result-image__element, img').first().attr('data-src') ||
      node.find('img').first().attr('src') ||
      '';
    const idMatch = mlUrl.match(/(ML[A-Z]-?\d+)/);

    if (title && !isNaN(price) && mlUrl && idMatch) {
      products.push({
        mlId: idMatch[1].replace('-', ''),
        title,
        price,
        imageUrl,
        mlUrl,
      });
    }
  });

  return products;
}

async function saveProducts(category: string, products: ScrapedProduct[]): Promise<number> {
  const batch = db.batch();
  const now = Date.now();
  for (const product of products) {
    const ref = db.collection('products').doc(product.mlId);
    batch.set(
      ref,
      {
        title: product.title,
        price: product.price,
        currency: 'CLP',
        imageUrl: product.imageUrl,
        mlUrl: product.mlUrl,
        mlId: product.mlId,
        category,
        lastScrapedAt: now,
      },
      { merge: true }
    );
  }
  await batch.commit();
  return products.length;
}

export const refreshStoreProducts = onCall<{ query: string }>(async (request) => {
  const uid = request.auth?.uid;
  if (!uid) throw new HttpsError('unauthenticated', 'Debes iniciar sesion.');

  const userSnap = await db.collection('users').doc(uid).get();
  const role = userSnap.exists ? (userSnap.data() as any).role : null;
  if (role !== 'admin' && role !== 'coach') {
    throw new HttpsError('permission-denied', 'Solo un administrador puede actualizar la tienda.');
  }

  const { query } = request.data;
  if (!query) throw new HttpsError('invalid-argument', 'Falta el termino de busqueda.');

  try {
    const products = await scrapeSearch(query);
    const added = await saveProducts(query, products);
    return { added };
  } catch (err) {
    logger.error(`Error al scrapear "${query}"`, err);
    throw new HttpsError('internal', 'No se pudo actualizar el catalogo desde Mercado Libre.');
  }
});

export const refreshStoreProductsScheduled = onSchedule('every 24 hours', async () => {
  for (const query of DEFAULT_QUERIES) {
    try {
      const products = await scrapeSearch(query);
      const added = await saveProducts(query, products);
      logger.info(`Catalogo actualizado para "${query}": ${added} productos`);
    } catch (err) {
      logger.error(`Error al scrapear "${query}" (job programado)`, err);
    }
  }
});
