using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using System.Collections.Generic;
using System.Text.RegularExpressions;

using Serilog;
using RestSharp;
using RestSharp.Serializers.SystemTextJson;
using AngleSharp.Html.Parser;

using BibleBot.Lib;
using BibleBot.Backend.Models;

namespace BibleBot.Backend.Services.Providers
{
    public class APIBibleProvider : IBibleProvider
    {
        public string Name { get; set; }
        private readonly RestClient _restClient;
        private readonly HtmlParser _htmlParser;

        private readonly Dictionary<string, string> _versionTable;

        private readonly string _baseURL = "https://api.scripture.api.bible/v1";
        private readonly string _getURI = "bibles/{0}/search?query={1}&limit=1";
        private readonly string _searchURI = "bibles/{0}/search?query={1}&limit=100&sort=relevance";

        public APIBibleProvider()
        {
            Name = "ab";

            _restClient = new RestClient(_baseURL);
            _restClient.UseSystemTextJson(new JsonSerializerOptions { PropertyNameCaseInsensitive = true });

            _htmlParser = new HtmlParser();

            _versionTable = new Dictionary<string, string>
            {
                { "KJVA", "de4e12af7f28f599-01" }, // King James Version with Apocrypha
                { "FBV", "65eec8e0b60e656b-01" } // Free Bible Version
            };
        }

        public async Task<Verse> GetVerse(Reference reference, bool titlesEnabled, bool verseNumbersEnabled)
        {
            if (reference.Book != "str")
            {
                reference.AsString = reference.ToString();
            }

            string url = System.String.Format(_getURI, _versionTable[reference.Version.Abbreviation], reference.AsString);
            
            var req = new RestRequest(url);
            req.AddHeader("api-key", System.Environment.GetEnvironmentVariable("APIBIBLE_TOKEN"));

            ABSearchResponse resp = await _restClient.GetAsync<ABSearchResponse>(req);

            if (resp.Data == null)
            {
                return null;
            }

            if (resp.Data.Passages[0].BibleId != _versionTable[reference.Version.Abbreviation])
            {
                Log.Error($"{reference.Version.Abbreviation} machine broke");
                return null;
            }

            if (resp.Data.Passages[0].Content.Length < 1)
            {
                return null;
            }

            var document = await _htmlParser.ParseDocumentAsync(resp.Data.Passages[0].Content);

            var numbers = document.QuerySelectorAll(".v");

            foreach (var el in numbers)
            {
                if (verseNumbersEnabled)
                {
                    el.TextContent = $" <**{el.TextContent}**> ";
                }
                else
                {
                    el.Remove();
                }
            }

            string title = titlesEnabled ? System.String.Join(" / ", document.GetElementsByTagName("h3").Select(el => el.TextContent.Trim())) : "";
            string text = System.String.Join("\n", document.GetElementsByTagName("p").Select(el => el.TextContent.Trim()));

            // As the verse reference could have a non-English name...
            reference.AsString = resp.Data.Passages[0].Reference;

            return new Verse { Reference = reference, Title = title, PsalmTitle = "", Text = PurifyVerseText(text) };
        }

        public async Task<Verse> GetVerse(string reference, bool titlesEnabled, bool verseNumbersEnabled, Version version)
        {
            return await GetVerse(new Reference{ Book = "str", Version = version, AsString = reference }, titlesEnabled, verseNumbersEnabled);
        }

        public async Task<List<SearchResult>> Search(string query, Version version)
        {
            string url = System.String.Format(_searchURI, _versionTable[version.Abbreviation], query);
            
            var req = new RestRequest(url);
            req.AddHeader("api-key", System.Environment.GetEnvironmentVariable("APIBIBLE_TOKEN"));
            
            ABSearchResponse resp = await _restClient.GetAsync<ABSearchResponse>(req);

            var results = new List<SearchResult>();

            if (resp.Data != null)
            {
                foreach (var verse in resp.Data.Verses)
                {
                    results.Add(new SearchResult
                    {
                        Reference = verse.Reference,
                        Text = PurifyVerseText(verse.Text)
                    });
                }
            }

            return results;
        }

        private string PurifyVerseText(string text)
        {
            Dictionary<string, string> nuisances = new Dictionary<string, string>
            {
		        { "“",     "\"" },
		        { "”",     "\"" },
		        { "\n",    " " },
                { "\t",    " " },
                { "\v",    " " },
                { "\f",    " " },
                { "\r",    " " },
		        { "¶ ",    "" },
		        { " , ",   ", " },
		        { " .",    "." },
		        { "′",     "'" },
		        { " . ",   " " },
            };

            if (text.Contains("Selah."))
            {
                text = text.Replace("Selah.", " *(Selah)* ");
            }
            else if (text.Contains("Selah"))
            {
                text = text.Replace("Selah", " *(Selah)* ");
            }

            foreach (var pair in nuisances)
            {
                if (text.Contains(pair.Key))
                {
                    text = text.Replace(pair.Key, pair.Value);
                }
            }

            text = Regex.Replace(text, @"\s+", " ");

            return text.Trim();
        }
    }
}